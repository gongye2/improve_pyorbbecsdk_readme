# ******************************************************************************
#  Copyright (c) 2024 Orbbec 3D Technology, Inc
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ******************************************************************************
"""
Performance tests: Frame drop detection, CPU/IO stress, resource monitoring.

Ported from C++ perf_test.cpp:
  TC_PERF_01_frame_drop_detection
  TC_PERF_02_frame_drop_under_cpu_stress
  TC_PERF_03_frame_drop_under_io_stress

Configuration via environment variables:
  PERF_DURATION_SECONDS  — test duration (default: 15)
  PERF_CPU_THREADS       — CPU stress thread count (default: os.cpu_count())
  PERF_IO_THREADS        — IO stress thread count (default: 2)

Usage:
    pytest test/test_perf_frame_drop.py -v
    PERF_DURATION_SECONDS=10 pytest test/test_perf_frame_drop.py -v -k baseline
"""

import os
import tempfile
import threading
import time
from dataclasses import dataclass, field

import pytest

from pyorbbecsdk import (
    Config,
    OBFrameAggregateOutputMode,
    OBFrameType,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.performance]


# ===================================================================
# PerfConfig — runtime configuration (env vars > defaults)
# ===================================================================
class PerfConfig:
    _duration_sec = int(os.environ.get("PERF_DURATION_SECONDS", "15"))
    _cpu_threads = int(os.environ.get("PERF_CPU_THREADS", str(os.cpu_count() or 4)))
    _io_threads = int(os.environ.get("PERF_IO_THREADS", "2"))

    @classmethod
    def duration_sec(cls) -> int:
        return cls._duration_sec

    @classmethod
    def cpu_threads(cls) -> int:
        return cls._cpu_threads

    @classmethod
    def io_threads(cls) -> int:
        return cls._io_threads


# ===================================================================
# Stream label / frame-type normalization
# ===================================================================
def _stream_label(ftype: OBFrameType) -> str:
    mapping = {
        OBFrameType.DEPTH_FRAME: "depth",
        OBFrameType.COLOR_FRAME: "color",
        OBFrameType.IR_FRAME: "ir",
        OBFrameType.LEFT_IR_FRAME: "ir",
        OBFrameType.RIGHT_IR_FRAME: "ir",
    }
    return mapping.get(ftype, f"other_{int(ftype)}")


def _normalize_frame_type(ftype: OBFrameType) -> OBFrameType:
    if ftype in (OBFrameType.LEFT_IR_FRAME, OBFrameType.RIGHT_IR_FRAME):
        return OBFrameType.IR_FRAME
    return ftype


_VALID_TYPES = {
    OBFrameType.DEPTH_FRAME,
    OBFrameType.COLOR_FRAME,
    OBFrameType.IR_FRAME,
}


# ===================================================================
# Per-stream statistics accumulator
# ===================================================================
@dataclass
class StreamStats:
    stream_name: str = ""
    total_frames: int = 0
    fps: int = 0
    expected_interval_us: float = 0.0

    # frame-index continuity
    prev_meta_frame_number: int = -1
    prev_sdk_index: int = 0
    meta_index_drops: int = 0
    sdk_index_drops: int = 0

    # timestamp continuity
    prev_hw_ts: int = 0
    prev_sys_ts: int = 0
    prev_global_ts: int = 0
    hw_ts_anomalies: int = 0
    sys_ts_anomalies: int = 0
    global_ts_anomalies: int = 0


# ===================================================================
# CpuStressor — saturates CPU with busy-loop threads
# ===================================================================
class CpuStressor:
    def __init__(self):
        self._running = False
        self._threads: list[threading.Thread] = []

    def start(self, num_threads: int = 0):
        if num_threads <= 0:
            num_threads = os.cpu_count() or 4
        self._running = True
        for i in range(num_threads):
            t = threading.Thread(target=self._busy_loop, name=f"cpu_stress_{i}", daemon=True)
            t.start()
            self._threads.append(t)
        print(f"[CpuStressor] Started {num_threads} stress threads")

    def stop(self):
        self._running = False
        for t in self._threads:
            t.join(timeout=5)
        self._threads.clear()

    @staticmethod
    def _busy_loop():
        import math

        val = 1.0
        while threading.current_thread().name.startswith("cpu_stress"):
            # Check a thread-safe flag via module-level attribute
            # Since we can't easily pass the event, use a short sleep approach
            for _ in range(10000):
                val = val * 1.000001 + 0.000001
                if val > 1e10:
                    val = 1.0
            # Brief yield so stop() can be noticed
            time.sleep(0.001)


# ===================================================================
# IoStressor — heavy file read/write in a loop
# ===================================================================
class IoStressor:
    def __init__(self):
        self._running = False
        self._threads: list[threading.Thread] = []
        self._tmpdir = tempfile.mkdtemp(prefix="pyorbbec_perf_")

    def start(self, num_threads: int = 2):
        self._running = True
        for i in range(num_threads):
            t = threading.Thread(target=self._io_loop, args=(i,), name=f"io_stress_{i}", daemon=True)
            t.start()
            self._threads.append(t)
        print(f"[IoStressor] Started {num_threads} IO stress threads (tmpdir={self._tmpdir})")

    def stop(self):
        self._running = False
        for t in self._threads:
            t.join(timeout=5)
        self._threads.clear()
        # Cleanup temp files
        try:
            import shutil

            shutil.rmtree(self._tmpdir, ignore_errors=True)
        except Exception:
            pass

    def _io_loop(self, index: int):
        filename = os.path.join(self._tmpdir, f"perf_io_{index}.tmp")
        buf = b"X" * (1024 * 1024)  # 1 MB

        while self._running:
            # Write ~10 MB
            try:
                with open(filename, "wb") as f:
                    for _ in range(10):
                        if not self._running:
                            break
                        f.write(buf)
            except Exception:
                pass
            # Read back
            try:
                with open(filename, "rb") as f:
                    while self._running and f.read(1024 * 1024):
                        pass
            except Exception:
                pass
            time.sleep(0.01)


# ===================================================================
# ResourceMonitor — samples CPU% and memory every second
# ===================================================================
class ResourceMonitor:
    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None
        self._samples: list[tuple[float, float, float]] = []  # (elapsed, cpu%, mem_mb)
        self._start_time: float = 0
        self._lock = threading.Lock()

    @property
    def samples(self):
        return list(self._samples)

    def start(self):
        self._samples.clear()
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="resource_monitor")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def save_csv(self, prefix: str):
        path = f"{prefix}_resource.csv"
        try:
            with open(path, "w") as f:
                f.write("ElapsedSec,CPU_Percent,Memory_MB\n")
                with self._lock:
                    for elapsed, cpu, mem in self._samples:
                        f.write(f"{elapsed:.2f},{cpu:.2f},{mem:.2f}\n")
            print(f"[ResourceMonitor] Saved: {path}")
        except Exception as e:
            print(f"[ResourceMonitor] Failed to save CSV: {e}")

    def _monitor_loop(self):
        while self._running:
            time.sleep(1)
            if not self._running:
                break
            elapsed = time.time() - self._start_time
            cpu = self._get_cpu_percent()
            mem = self._get_memory_mb()
            with self._lock:
                self._samples.append((elapsed, cpu, mem))

    @staticmethod
    def _get_cpu_percent() -> float:
        try:
            import psutil

            proc = psutil.Process(os.getpid())
            # Use interval=1 for accurate measurement over 1 second window
            return proc.cpu_percent(interval=1)
        except ImportError:
            return -1.0

    @staticmethod
    def _get_memory_mb() -> float:
        try:
            import psutil

            proc = psutil.Process(os.getpid())
            return proc.memory_info().rss / (1024 * 1024)
        except ImportError:
            return -1.0


# ===================================================================
# PerfStreamTest — shared streaming driver
# ===================================================================
class PerfStreamTest:
    """Shared infrastructure for all perf tests. Not a pytest class itself."""

    def __init__(self, pipeline: Pipeline, duration_sec: int):
        self.pipeline = pipeline
        self.duration_sec = duration_sec
        self.lock = threading.Lock()
        self.stats_map: dict[OBFrameType, StreamStats] = {}
        self.csv_files: dict[OBFrameType, object] = {}
        self.csv_prefix = ""
        self.resource_monitor = ResourceMonitor()

    def process_frame(self, frame):
        """Process a single frame, updating stats and writing CSV."""
        if frame is None:
            return

        ntype = _normalize_frame_type(frame.get_type())
        if ntype not in _VALID_TYPES:
            return

        # Gather frame data
        sdk_index = frame.get_index()
        hw_ts = frame.get_timestamp_us()
        sys_ts = frame.get_system_timestamp_us()
        global_ts = frame.get_global_timestamp_us()

        meta_fn = -1
        try:
            from pyorbbecsdk import OBFrameMetadataType

            if frame.has_metadata(OBFrameMetadataType.FRAME_NUMBER):
                meta_fn = frame.get_metadata_value(OBFrameMetadataType.FRAME_NUMBER)
        except Exception:
            pass

        fps = 0
        try:
            profile = frame.get_stream_profile()
            if profile:
                fps = profile.get_fps()
        except Exception:
            pass

        with self.lock:
            st = self.stats_map.get(ntype)
            if st is None:
                st = StreamStats(stream_name=_stream_label(ntype))
                self.stats_map[ntype] = st

            if st.total_frames == 0:
                st.fps = fps if fps > 0 else 30
                st.expected_interval_us = 1e6 / st.fps if st.fps > 0 else 0

            if st.total_frames > 0:
                # SDK index continuity
                if sdk_index != st.prev_sdk_index + 1:
                    st.sdk_index_drops += 1

                # Metadata HW frame-number continuity
                if meta_fn >= 0 and st.prev_meta_frame_number >= 0:
                    if meta_fn != st.prev_meta_frame_number + 1:
                        st.meta_index_drops += 1

                # Timestamp continuity
                if st.expected_interval_us > 0:
                    tolerance = st.expected_interval_us * 0.5

                    if st.prev_hw_ts > 0 and hw_ts > 0:
                        diff = abs(hw_ts - st.prev_hw_ts)
                        if abs(diff - st.expected_interval_us) > tolerance:
                            st.hw_ts_anomalies += 1

                    if st.prev_sys_ts > 0 and sys_ts > 0:
                        diff = abs(sys_ts - st.prev_sys_ts)
                        if abs(diff - st.expected_interval_us) > tolerance:
                            st.sys_ts_anomalies += 1

                    if st.prev_global_ts > 0 and global_ts > 0:
                        diff = abs(global_ts - st.prev_global_ts)
                        if abs(diff - st.expected_interval_us) > tolerance:
                            st.global_ts_anomalies += 1

            st.prev_sdk_index = sdk_index
            st.prev_meta_frame_number = meta_fn
            st.prev_hw_ts = hw_ts
            st.prev_sys_ts = sys_ts
            st.prev_global_ts = global_ts
            st.total_frames += 1

            # Write CSV row
            self._write_csv_row(ntype, sdk_index, meta_fn, hw_ts, sys_ts, global_ts, fps)

    def open_csv(self, ftype: OBFrameType):
        """Open a per-stream CSV file for writing."""
        name = f"{self.csv_prefix}_{_stream_label(ftype)}_frames.csv"
        try:
            f = open(name, "w")
            f.write("SdkIndex,MetaFrameNumber,HwTimestamp_us,SysTimestamp_us,GlobalTimestamp_us,FPS\n")
            self.csv_files[ftype] = f
        except Exception:
            pass

    def _write_csv_row(self, ftype, sdk_index, meta_fn, hw_ts, sys_ts, global_ts, fps):
        csv_file = self.csv_files.get(ftype)
        if csv_file and not csv_file.closed:
            try:
                csv_file.write(f"{sdk_index},{meta_fn},{hw_ts},{sys_ts},{global_ts},{fps}\n")
            except Exception:
                pass

    def close_csv(self):
        for f in self.csv_files.values():
            if f and not f.closed:
                try:
                    f.flush()
                    f.close()
                except Exception:
                    pass
        self.csv_files.clear()

    def run_streaming_test(self, prefix: str):
        """Run the shared streaming test logic."""
        self.csv_prefix = prefix
        self.stats_map.clear()

        config = Config()
        config.enable_stream(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(OBSensorType.COLOR_SENSOR)
        config.set_frame_aggregate_output_mode(OBFrameAggregateOutputMode.DISABLE)

        # Try to enable IR stream as well
        ir_enabled = False
        try:
            config.enable_stream(OBSensorType.IR_SENSOR)
            ir_enabled = True
        except Exception:
            pass

        # Open per-stream CSV files
        self.open_csv(OBFrameType.DEPTH_FRAME)
        self.open_csv(OBFrameType.COLOR_FRAME)
        if ir_enabled:
            self.open_csv(OBFrameType.IR_FRAME)

        # Start resource monitor
        self.resource_monitor.start()

        # Pipeline callback
        def callback(frameset):
            if frameset is None:
                return
            count = frameset.get_count()
            for i in range(count):
                try:
                    frame = frameset.get_frame_by_index(i)
                    if frame:
                        self.process_frame(frame)
                except Exception:
                    pass

        # Start pipeline with callback (try with IR first, fallback without)
        started = False
        try:
            self.pipeline.start(config, callback)
            started = True
        except Exception:
            if ir_enabled:
                print(f"[PerfTest] Start with depth+color+IR failed, retrying without IR")
                config2 = Config()
                config2.enable_stream(OBSensorType.DEPTH_SENSOR)
                config2.enable_stream(OBSensorType.COLOR_SENSOR)
                config2.set_frame_aggregate_output_mode(OBFrameAggregateOutputMode.DISABLE)
                self.pipeline.start(config2, callback)
                started = True

        if not started:
            pytest.skip("Failed to start pipeline")

        print(f"[PerfTest] Streaming ({prefix}) for {self.duration_sec}s ...")
        time.sleep(self.duration_sec)

        self.pipeline.stop()
        self.resource_monitor.stop()

        # Save reports
        self.resource_monitor.save_csv(prefix)
        self.close_csv()

        # Print summary
        self._print_summary(prefix)

    def _print_summary(self, prefix: str):
        print(f"\n========== Performance Test Summary [{prefix}] ==========")
        print(f"Duration: {self.duration_sec} seconds\n")

        with self.lock:
            for ntype, st in sorted(self.stats_map.items(), key=lambda x: int(x[0])):
                print(f"--- {st.stream_name} (fps={st.fps}) ---")
                print(f"  Total frames:              {st.total_frames}")
                print(f"  SDK index discontinuities: {st.sdk_index_drops}")
                print(f"  Meta HW index drops:       {st.meta_index_drops}")
                print(f"  HW timestamp anomalies:    {st.hw_ts_anomalies}")
                print(f"  Sys timestamp anomalies:   {st.sys_ts_anomalies}")
                print(f"  Global ts anomalies:       {st.global_ts_anomalies}")
                print(f"  Expected interval (us):    {st.expected_interval_us:.1f}\n")

        samples = self.resource_monitor.samples
        if samples:
            cpus = [s[1] for s in samples if s[1] >= 0]
            mems = [s[2] for s in samples if s[2] >= 0]
            if cpus:
                print("--- Resource Usage ---")
                print(f"  Avg CPU: {sum(cpus)/len(cpus):.2f} %")
                print(f"  Max CPU: {max(cpus):.2f} %")
            if mems:
                print(f"  Avg Mem: {sum(mems)/len(mems):.2f} MB")
                print(f"  Max Mem: {max(mems):.2f} MB")

        print("====================================================")

    def assert_drop_rate(self, max_rate: float):
        """Assert that the meta-index drop rate is within threshold."""
        with self.lock:
            for ntype, st in self.stats_map.items():
                assert st.total_frames > 0, f"{st.stream_name}: received 0 frames in {self.duration_sec}s"
                if st.total_frames == 0:
                    continue
                drop_rate = st.meta_index_drops / st.total_frames
                assert drop_rate < max_rate, (
                    f"{st.stream_name} meta-index drop rate: {drop_rate * 100:.2f}% "
                    f"({st.meta_index_drops} / {st.total_frames})"
                )

    def cleanup(self):
        self.resource_monitor.stop()
        self.close_csv()


# ===================================================================
# TC_PERF_01 — Baseline frame-drop detection
# ===================================================================
class TC_PERF_01_FrameDrop:
    """Tests for baseline frame-drop detection."""

    def test_frame_drop_detection(self, device, pipeline: Pipeline):
        """TC_PERF_01: Baseline frame-drop detection over test duration."""
        duration = PerfConfig.duration_sec()
        test = PerfStreamTest(pipeline, duration)
        try:
            test.run_streaming_test("baseline")
            test.assert_drop_rate(0.01)  # expect < 1% drop
        finally:
            test.cleanup()


# ===================================================================
# TC_PERF_02 — Frame-drop under CPU stress
# ===================================================================
class TC_PERF_02_CpuStress:
    """Tests for frame-drop under CPU stress."""

    def test_frame_drop_under_cpu_stress(self, device, pipeline: Pipeline):
        """TC_PERF_02: Frame-drop detection while CPU is saturated."""
        duration = PerfConfig.duration_sec()
        stressor = CpuStressor()
        stressor.start(PerfConfig.cpu_threads())

        test = PerfStreamTest(pipeline, duration)
        try:
            test.run_streaming_test("cpu_stress")
            test.assert_drop_rate(0.05)  # allow up to 5% under stress
        finally:
            test.cleanup()
            stressor.stop()


# ===================================================================
# TC_PERF_03 — Frame-drop under IO stress
# ===================================================================
class TC_PERF_03_IoStress:
    """Tests for frame-drop under IO stress."""

    def test_frame_drop_under_io_stress(self, device, pipeline: Pipeline):
        """TC_PERF_03: Frame-drop detection while IO is saturated."""
        duration = PerfConfig.duration_sec()
        stressor = IoStressor()
        stressor.start(PerfConfig.io_threads())

        test = PerfStreamTest(pipeline, duration)
        try:
            test.run_streaming_test("io_stress")
            test.assert_drop_rate(0.05)  # allow up to 5% under stress
        finally:
            test.cleanup()
            stressor.stop()
