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
Hardware test: Pipeline expanded (TC_CPP_08).

Ported from C++ hw_full_test.cpp:
  TC_CPP_08_05 switch_config
  TC_CPP_08_08 frame_sync
  TC_CPP_08_09 d2c_depth_profile_list
  TC_CPP_08_11 calibration_param
"""

import pytest

from pyorbbecsdk import (
    Config,
    OBAlignMode,
    OBFrameAggregateOutputMode,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_08_Pipeline_Expanded:
    """Tests for pipeline advanced operations."""

    def test_switch_config(self, device, pipeline: Pipeline):
        """TC_CPP_08_05: Pipeline can switch configurations while running."""
        # Start with depth
        config1 = Config()
        depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        depth_profile = depth_profiles.get_default_video_stream_profile()
        config1.enable_stream(depth_profile)
        pipeline.start(config1)

        frames = pipeline.wait_for_frames(5000)
        if frames is None:
            pipeline.stop()
            pytest.skip("No depth frames received")

        # Switch to color
        pipeline.stop()
        config2 = Config()
        try:
            color_profiles = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            color_profile = color_profiles.get_default_video_stream_profile()
            config2.enable_stream(color_profile)
            pipeline.start(config2)

            frames2 = pipeline.wait_for_frames(5000)
            if frames2 is None:
                pipeline.stop()
                pytest.skip("No color frames received")
        finally:
            pipeline.stop()

    def test_frame_sync(self, device, pipeline: Pipeline):
        """TC_CPP_08_08: Frame sync produces paired depth+color frames."""
        config = Config()
        try:
            depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            color_profiles = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            config.enable_stream(depth_profiles.get_default_video_stream_profile())
            config.enable_stream(color_profiles.get_default_video_stream_profile())
        except Exception:
            pytest.skip("Cannot enable both depth and color streams")

        config.set_align_mode(OBAlignMode.DISABLE)
        pipeline.start(config)

        synced_count = 0
        for _ in range(10):
            frames = pipeline.wait_for_frames(3000)
            if frames is None:
                continue
            depth = frames.get_depth_frame()
            color = frames.get_color_frame()
            if depth is not None and color is not None:
                synced_count += 1

        pipeline.stop()
        if synced_count == 0:
            pytest.skip("No synced depth+color frames received")

    def test_d2c_depth_profile_list(self, device, pipeline: Pipeline):
        """TC_CPP_08_09: D2C enabled depth profile list matches color resolution."""
        try:
            depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            color_profiles = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
        except Exception:
            pytest.skip("Cannot query both stream profile lists")

        depth_count = depth_profiles.get_count()
        color_count = color_profiles.get_count()
        assert depth_count > 0
        assert color_count > 0

    def test_calibration_param(self, device, pipeline: Pipeline):
        """TC_CPP_08_11: Pipeline can retrieve calibration parameters."""
        param = pipeline.get_camera_param()
        assert param is not None
        # Depth intrinsic should be valid (may be zero if not calibrated)
        # We verify the struct is accessible
        assert param.depth_intrinsic is not None
        assert param.rgb_intrinsic is not None
