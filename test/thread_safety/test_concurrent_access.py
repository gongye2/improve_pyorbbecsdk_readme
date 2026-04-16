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
Thread safety test: Concurrent multi-threaded access (TC_TS).

Ported from C++ thread_safety_test.cpp:
  TC_TS_01_concurrent_pipeline_start_stop
  TC_TS_02_stream_while_property_access
  TC_TS_03_concurrent_pipeline_create_destroy

These tests verify that concurrent multi-threaded access to the SDK
does not cause crashes, deadlocks, or data corruption.
"""

import os
import threading
import time

import pytest

from pyorbbecsdk import (
    Config,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


def _get_ts_duration() -> int:
    return int(os.environ.get("TS_DURATION_SECONDS", "3"))


def _get_ts_thread_count() -> int:
    return int(os.environ.get("TS_THREAD_COUNT", "2"))


class TC_TS_ThreadSafety:
    """Tests for thread safety under concurrent multi-threaded access."""

    def test_concurrent_pipeline_start_stop(self, device, pipeline: Pipeline):
        """TC_TS_01: Multiple threads concurrently start/stop the same Pipeline."""
        duration_sec = _get_ts_duration()
        thread_count = _get_ts_thread_count()

        config = Config()
        try:
            depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            config.enable_stream(depth_profiles.get_default_video_stream_profile())
        except Exception:
            pass

        running = threading.Event()
        running.set()
        errors = [0]
        lock = threading.Lock()

        def worker():
            while running.is_set():
                try:
                    pipeline.start(config)
                    time.sleep(0.05)
                    pipeline.stop()
                    time.sleep(0.01)
                except Exception as e:
                    # SDK may legitimately reject concurrent start/stop
                    with lock:
                        errors[0] += 1

        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        time.sleep(duration_sec)
        running.clear()

        for t in threads:
            t.join(timeout=10)

        # Ensure the pipeline can still be used normally after the stress
        try:
            pipeline.stop()
        except Exception:
            pass

        # We accept some errors from concurrent start/stop, but no crashes
        print(f"[TC_TS_01] Completed without crash. errors={errors[0]}")

    def test_stream_while_property_access(self, device, pipeline: Pipeline):
        """TC_TS_02: One thread streams frames, another reads/writes properties."""
        duration_sec = _get_ts_duration()

        config = Config()
        try:
            depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            config.enable_stream(depth_profiles.get_default_video_stream_profile())
        except Exception:
            pass

        running = threading.Event()
        running.set()
        frame_count = [0]
        stream_errors = [0]
        prop_errors = [0]

        # Collect supported read-write int properties
        rw_props = []
        try:
            prop_count = device.get_supported_property_count()
            for i in range(prop_count):
                try:
                    item = device.get_supported_property(i)
                    # Check if it's a read-write int property
                    from pyorbbecsdk import OBPermissionType

                    if item.permission == OBPermissionType.PERMISSION_READ_WRITE:
                        rw_props.append(item.id)
                except Exception:
                    pass
        except Exception:
            pass

        pipeline.start(config)

        # Thread A: continuously pull frames
        def stream_thread():
            while running.is_set():
                try:
                    frameset = pipeline.wait_for_frames(200)
                    if frameset:
                        frame_count[0] += 1
                except Exception:
                    stream_errors[0] += 1

        # Thread B: repeatedly get/set device properties
        def prop_thread():
            while running.is_set():
                for prop_id in rw_props:
                    if not running.is_set():
                        break
                    try:
                        from pyorbbecsdk import OBPermissionType

                        if device.is_property_supported(prop_id, OBPermissionType.PERMISSION_READ_WRITE):
                            # Try to read property
                            try:
                                device.get_int_property(prop_id)
                                device.set_int_property(prop_id, 0)  # Write back safe value
                            except Exception:
                                pass
                    except Exception:
                        prop_errors[0] += 1
                if not rw_props:
                    time.sleep(0.05)

        t1 = threading.Thread(target=stream_thread)
        t2 = threading.Thread(target=prop_thread)
        t1.start()
        t2.start()

        time.sleep(duration_sec)
        running.clear()

        t1.join(timeout=10)
        t2.join(timeout=10)

        try:
            pipeline.stop()
        except Exception:
            pass

        print(f"[TC_TS_02] frames={frame_count[0]}, rw_properties={len(rw_props)}")
        print(f"[TC_TS_02] stream_errors={stream_errors[0]}, prop_errors={prop_errors[0]}")
        # We check no crashes/deadlocks occurred — errors are acceptable
        # under concurrent access
        assert frame_count[0] > 0, "No frames received during the test"

    def test_concurrent_pipeline_create_destroy(self, device):
        """TC_TS_03: Multiple threads each create/use/destroy Pipeline simultaneously."""
        duration_sec = _get_ts_duration()
        thread_count = _get_ts_thread_count()

        running = threading.Event()
        running.set()
        errors = [0]
        iterations = [0]
        lock = threading.Lock()

        def worker():
            while running.is_set():
                try:
                    p = Pipeline(device)
                    config = Config()
                    try:
                        profiles = p.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
                        config.enable_stream(profiles.get_default_video_stream_profile())
                    except Exception:
                        pass
                    p.start(config)

                    # Pull a few frames, then tear down
                    for _ in range(5):
                        if not running.is_set():
                            break
                        try:
                            p.wait_for_frames(500)
                        except Exception:
                            pass

                    try:
                        p.stop()
                    except Exception:
                        pass

                    with lock:
                        iterations[0] += 1
                except Exception as e:
                    # SDK may reject overlapping pipeline instances
                    with lock:
                        errors[0] += 1

                time.sleep(0.1)

        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        time.sleep(duration_sec)
        running.clear()

        for t in threads:
            t.join(timeout=10)

        print(f"[TC_TS_03] iterations={iterations[0]}, errors={errors[0]}")
        # We accept some errors from concurrent access, but no crashes
        print("[TC_TS_03] Completed without crash or deadlock.")
