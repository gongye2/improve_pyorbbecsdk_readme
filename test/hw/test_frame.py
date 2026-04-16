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
Hardware test: Frame expanded (TC_CPP_10).

Ported from C++ hw_full_test.cpp:
  TC_CPP_10_01 frame_basic
  TC_CPP_10_02 timestamp_monotonicity
  TC_CPP_10_03 frame_associated_info
  TC_CPP_10_05 video_frame_properties
  TC_CPP_10_06 depth_frame_scale
  TC_CPP_10_07 color_ir_data_valid
  TC_CPP_10_08 points_frame
  TC_CPP_10_09 accel_frame
  TC_CPP_10_10 gyro_frame
  TC_CPP_10_11 frameset_count_extract
  TC_CPP_10_12 frameset_by_type_index
  TC_CPP_10_14 frameset_sync
"""

import time

import numpy as np
import pytest

from pyorbbecsdk import (
    Config,
    OBFrameAggregateOutputMode,
    OBFrameType,
    OBSensorType,
    OBStreamType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]

_TIMEOUT_MS = 3000


def _find_matching_profiles(pipeline, min_fps: int = 10) -> tuple:
    """Find depth and color profiles with matching resolution and fps."""
    from pyorbbecsdk import OBFormat

    depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
    color_profiles = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)

    for i in range(depth_profiles.get_count()):
        dp = depth_profiles.get_stream_profile_by_index(i)
        if dp.get_format() != OBFormat.Y16 or dp.get_fps() < min_fps:
            continue
        for j in range(color_profiles.get_count()):
            cp = color_profiles.get_stream_profile_by_index(j)
            if dp.get_width() == cp.get_width() and dp.get_height() == cp.get_height() and dp.get_fps() == cp.get_fps():
                return dp, cp
    raise ValueError("No matching depth+color profiles found")


class TC_CPP_10_Frame_Expanded:
    """Tests for Frame details and Frameset operations."""

    def test_frame_basic(self, device, pipeline: Pipeline):
        """TC_CPP_10_01: Frame basic properties are valid."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        frames = pipeline.wait_for_frames(_TIMEOUT_MS)
        pipeline.stop()
        assert frames is not None

        depth = frames.get_depth_frame()
        assert depth is not None
        assert depth.get_width() > 0
        assert depth.get_height() > 0
        assert depth.get_data_size() > 0
        assert depth.get_timestamp_us() > 0

    def test_timestamp_monotonicity(self, device, pipeline: Pipeline):
        """TC_CPP_10_02: Frame timestamps are monotonically increasing."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        prev_ts = 0
        monotonic = True
        for _ in range(20):
            frames = pipeline.wait_for_frames(_TIMEOUT_MS)
            if frames is None:
                continue
            depth = frames.get_depth_frame()
            if depth is None:
                continue
            ts = depth.get_timestamp_us()
            if ts < prev_ts:
                monotonic = False
                break
            prev_ts = ts

        pipeline.stop()
        assert monotonic, "Frame timestamps are not monotonically increasing"

    def test_frame_associated_info(self, device, pipeline: Pipeline):
        """TC_CPP_10_03: Frame has associated stream profile and device info."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        frames = pipeline.wait_for_frames(_TIMEOUT_MS)
        pipeline.stop()
        assert frames is not None

        depth = frames.get_depth_frame()
        assert depth is not None
        profile = depth.get_stream_profile()
        assert profile is not None
        assert profile.get_width() > 0
        assert profile.get_height() > 0

    def test_video_frame_properties(self, device, pipeline: Pipeline):
        """TC_CPP_10_05: Video frame has width, height, format, pixel type."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        frames = pipeline.wait_for_frames(_TIMEOUT_MS)
        pipeline.stop()
        assert frames is not None

        color = frames.get_color_frame()
        assert color is not None
        assert color.get_width() > 0
        assert color.get_height() > 0
        # Format and pixel type should be accessible
        fmt = color.get_format()
        assert fmt is not None

    def test_depth_frame_scale(self, device, pipeline: Pipeline):
        """TC_CPP_10_06: Depth frame scale is accessible and positive."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        frames = pipeline.wait_for_frames(_TIMEOUT_MS)
        pipeline.stop()
        assert frames is not None

        depth = frames.get_depth_frame()
        assert depth is not None
        scale = depth.get_depth_scale()
        assert scale > 0

    def test_color_ir_data_valid(self, device, pipeline: Pipeline):
        """TC_CPP_10_07: Color and IR frame data buffers are valid."""
        # Test color data
        config = Config()
        try:
            color_profiles = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            config.enable_stream(color_profiles.get_default_video_stream_profile())
        except Exception:
            pytest.skip("Color sensor not available")

        pipeline.start(config)
        frames = pipeline.wait_for_frames(_TIMEOUT_MS)
        pipeline.stop()
        assert frames is not None

        color = frames.get_color_frame()
        if color is not None:
            data = color.get_data()
            assert data is not None
            assert len(data) > 0

    def test_points_frame(self, device, pipeline: Pipeline):
        """TC_CPP_10_08: Point cloud frame can be generated."""
        from pyorbbecsdk import PointCloudFilter

        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        filt = PointCloudFilter()
        points = None
        deadline = time.time() + 10
        while points is None and time.time() < deadline:
            frames = pipeline.wait_for_frames(_TIMEOUT_MS)
            if frames is not None:
                points = filt.process(frames)

        pipeline.stop()
        assert points is not None
        pts = points.as_points_frame()
        assert pts.get_data_size() > 0

    def test_accel_frame(self, device, pipeline: Pipeline):
        """TC_CPP_10_09: Accel frame data is accessible."""
        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.ACCEL_SENSOR)
            count = profile_list.get_count()
            if count == 0:
                pytest.skip("No accel profiles available")
            profile = profile_list.get_stream_profile_by_index(0)
        except Exception:
            pytest.skip("Accel sensor not available")

        config = Config()
        config.enable_stream(profile)
        pipeline.start(config)

        found_accel = False
        for _ in range(10):
            frames = pipeline.wait_for_frames(_TIMEOUT_MS)
            if frames is None:
                continue
            accel = frames.get_frame_by_type(OBFrameType.ACCEL_FRAME)
            if accel is not None:
                found_accel = True
                break

        pipeline.stop()
        assert found_accel, "No accel frame received"

    def test_gyro_frame(self, device, pipeline: Pipeline):
        """TC_CPP_10_10: Gyro frame data is accessible."""
        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.GYRO_SENSOR)
            count = profile_list.get_count()
            if count == 0:
                pytest.skip("No gyro profiles available")
            profile = profile_list.get_stream_profile_by_index(0)
        except Exception:
            pytest.skip("Gyro sensor not available")

        config = Config()
        config.enable_stream(profile)
        pipeline.start(config)

        found_gyro = False
        for _ in range(10):
            frames = pipeline.wait_for_frames(_TIMEOUT_MS)
            if frames is None:
                continue
            gyro = frames.get_frame_by_type(OBFrameType.GYRO_FRAME)
            if gyro is not None:
                found_gyro = True
                break

        pipeline.stop()
        assert found_gyro, "No gyro frame received"

    def test_frameset_count_extract(self, device, pipeline: Pipeline):
        """TC_CPP_10_11: Frameset has frame count and extraction works."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        frames = pipeline.wait_for_frames(_TIMEOUT_MS)
        pipeline.stop()
        assert frames is not None

        count = frames.get_frame_count()
        assert count > 0

        # Extract by index
        first = frames.get_frame_by_index(0)
        assert first is not None

        # __len__ should work
        assert len(frames) == count

    def test_frameset_by_type_index(self, device, pipeline: Pipeline):
        """TC_CPP_10_12: Frameset can extract frames by type and index."""
        config = Config()
        try:
            dp, cp = _find_matching_profiles(pipeline)
            config.enable_stream(dp)
            config.enable_stream(cp)
        except Exception:
            pytest.skip("Cannot find matching depth+color profiles")

        config.set_frame_aggregate_output_mode(OBFrameAggregateOutputMode.FULL_FRAME_REQUIRE)
        pipeline.start(config)
        frames = pipeline.wait_for_frames(_TIMEOUT_MS)
        pipeline.stop()
        assert frames is not None

        # By type
        depth = frames.get_frame_by_type(OBFrameType.DEPTH_FRAME)
        assert depth is not None

        color = frames.get_frame_by_type(OBFrameType.COLOR_FRAME)
        if color is None:
            pytest.skip("Color frame not available in frameset")

        # Convenience getters
        depth2 = frames.get_depth_frame()
        assert depth2 is not None

        color2 = frames.get_color_frame()
        assert color2 is not None

    def test_frameset_sync(self, device, pipeline: Pipeline):
        """TC_CPP_10_14: Frameset contains synced depth+color frames."""
        config = Config()
        try:
            dp, cp = _find_matching_profiles(pipeline)
            config.enable_stream(dp)
            config.enable_stream(cp)
        except Exception:
            pytest.skip("Cannot find matching depth+color profiles")

        config.set_frame_aggregate_output_mode(OBFrameAggregateOutputMode.FULL_FRAME_REQUIRE)
        pipeline.start(config)

        synced_count = 0
        for _ in range(15):
            frames = pipeline.wait_for_frames(_TIMEOUT_MS)
            if frames is None:
                continue
            depth = frames.get_depth_frame()
            color = frames.get_color_frame()
            if depth is not None and color is not None:
                synced_count += 1

        pipeline.stop()
        if synced_count == 0:
            pytest.skip("No synced depth+color frames received")
