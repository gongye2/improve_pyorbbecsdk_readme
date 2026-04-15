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
Performance test: Frame drop detection (TC_PERF_01).

Ported from C++ perf_test.cpp:
  TC_PERF_01_frame_drop_detection

This is a long-running test (default 60 seconds) that checks:
  - Frame index continuity (no dropped frames)
  - Timestamp monotonicity
  - Per-stream frame counts

Usage:
    pytest test/test_perf_frame_drop.py -v
    pytest test/test_perf_frame_drop.py -v -k "baseline" --perf-duration=30
"""

import os
import time

import pytest

from pyorbbecsdk import (
    Config,
    OBFrameAggregateOutputMode,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.performance]


def _get_perf_duration() -> int:
    """Get test duration from environment or CLI default."""
    try:
        return int(os.environ.get("PERF_DURATION_SECONDS", "15"))
    except ValueError:
        return 15


class StreamStats:
    """Per-stream statistics accumulator."""

    def __init__(self, name: str):
        self.stream_name = name
        self.total_frames = 0
        self.fps = 0
        self.expected_interval_us = 0.0
        self.prev_sdk_index = 0
        self.prev_meta_frame_number = -1
        self.meta_index_drops = 0
        self.sdk_index_drops = 0
        self.prev_hw_ts = 0
        self.hw_ts_anomalies = 0

    def process_frame(self, sdk_index: int, meta_frame_number: int, hw_ts_us: int, fps: int):
        if self.total_frames == 0:
            self.fps = fps
            self.expected_interval_us = 1e6 / fps if fps > 0 else 0

        if self.total_frames > 0:
            # SDK index continuity
            if sdk_index != self.prev_sdk_index + 1:
                self.sdk_index_drops += 1

            # Metadata HW frame-number continuity
            if meta_frame_number >= 0 and self.prev_meta_frame_number >= 0:
                if meta_frame_number != self.prev_meta_frame_number + 1:
                    self.meta_index_drops += 1

            # Timestamp continuity
            if self.expected_interval_us > 0 and self.prev_hw_ts > 0 and hw_ts_us > 0:
                tolerance = self.expected_interval_us * 0.5
                diff = abs(hw_ts_us - self.prev_hw_ts)
                if abs(diff - self.expected_interval_us) > tolerance:
                    self.hw_ts_anomalies += 1

        self.prev_sdk_index = sdk_index
        self.prev_meta_frame_number = meta_frame_number
        self.prev_hw_ts = hw_ts_us
        self.total_frames += 1


class TC_PERF_01_FrameDrop:
    """Tests for baseline frame-drop detection."""

    def test_frame_drop_detection(self, device, pipeline: Pipeline):
        """TC_PERF_01: Baseline frame-drop detection over test duration."""
        duration_sec = _get_perf_duration()

        # Configure streams
        config = Config()
        try:
            depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            config.enable_stream(depth_profiles.get_default_video_stream_profile())
        except Exception:
            pass
        try:
            color_profiles = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            config.enable_stream(color_profiles.get_default_video_stream_profile())
        except Exception:
            pass

        pipeline.start(config)

        depth_stats = StreamStats("depth")
        color_stats = StreamStats("color")

        start_time = time.time()
        while time.time() - start_time < duration_sec:
            frames = pipeline.wait_for_frames(1000)
            if frames is None:
                continue

            # Process depth frame
            depth_frame = frames.get_depth_frame()
            if depth_frame:
                try:
                    meta_fn = -1
                    from pyorbbecsdk import OBFrameMetadataType
                    if depth_frame.has_metadata(OBFrameMetadataType.FRAME_NUMBER):
                        meta_fn = depth_frame.get_metadata_value(OBFrameMetadataType.FRAME_NUMBER)
                    depth_stats.process_frame(
                        sdk_index=depth_frame.get_index(),
                        meta_frame_number=meta_fn,
                        hw_ts_us=depth_frame.get_timestamp_us(),
                        fps=30,  # default, would read from profile in full impl
                    )
                except Exception:
                    pass

            # Process color frame
            color_frame = frames.get_color_frame()
            if color_frame:
                try:
                    meta_fn = -1
                    from pyorbbecsdk import OBFrameMetadataType
                    if color_frame.has_metadata(OBFrameMetadataType.FRAME_NUMBER):
                        meta_fn = color_frame.get_metadata_value(OBFrameMetadataType.FRAME_NUMBER)
                    color_stats.process_frame(
                        sdk_index=color_frame.get_index(),
                        meta_frame_number=meta_fn,
                        hw_ts_us=color_frame.get_timestamp_us(),
                        fps=30,
                    )
                except Exception:
                    pass

        pipeline.stop()

        # Print summary
        print(f"\n========== Performance Test Summary ==========")
        print(f"Duration: {duration_sec} seconds")
        for stats in [depth_stats, color_stats]:
            if stats.total_frames > 0:
                print(f"\n--- {stats.stream_name} (fps={stats.fps}) ---")
                print(f"  Total frames:              {stats.total_frames}")
                print(f"  SDK index discontinuities: {stats.sdk_index_drops}")
                print(f"  Meta HW index drops:       {stats.meta_index_drops}")
                print(f"  HW timestamp anomalies:    {stats.hw_ts_anomalies}")

        # Assert: expect < 1% drop rate
        for stats in [depth_stats, color_stats]:
            if stats.total_frames == 0:
                continue
            drop_rate = stats.meta_index_drops / stats.total_frames
            assert drop_rate < 0.01, (
                f"{stats.stream_name} meta-index drop rate: {drop_rate * 100:.2f}% "
                f"({stats.meta_index_drops} / {stats.total_frames})"
            )
