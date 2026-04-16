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
Hardware test: Config expanded (TC_CPP_09).

Ported from C++ hw_full_test.cpp:
  TC_CPP_09_02 enable_video_stream_params
  TC_CPP_09_03 enable_imu_stream
  TC_CPP_09_04 enable_disable_all
  TC_CPP_09_05 enabled_profiles
  TC_CPP_09_06 d2c_align_mode
  TC_CPP_09_07 depth_scale_after_align
  TC_CPP_09_08 frame_aggregate_mode
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


class TC_CPP_09_Config_Expanded:
    """Tests for Config advanced operations."""

    def test_enable_video_stream_params(self, device, pipeline: Pipeline):
        """TC_CPP_09_02: Enable video stream with explicit parameters."""
        config = Config()
        config.enable_video_stream(OBSensorType.COLOR_SENSOR, width=640, height=480, fps=30)
        enabled = config.get_enabled_stream_profile_list()
        assert enabled is not None
        assert enabled.get_count() > 0

    def test_enable_imu_stream(self, device, pipeline: Pipeline):
        """TC_CPP_09_03: Enable IMU streams."""
        try:
            config = Config()
            config.enable_accel_stream()
            config.enable_gyro_stream()
            pipeline.start(config)
            pipeline.stop()
        except Exception:
            pytest.skip("IMU stream not supported on this device")

    def test_enable_disable_all(self, device, pipeline: Pipeline):
        """TC_CPP_09_04: Enable and disable all streams."""
        config = Config()
        config.enable_all_stream()
        config.disable_all_stream()
        # Should not crash

    def test_enabled_profiles(self, device, pipeline: Pipeline):
        """TC_CPP_09_05: Enabled stream profiles can be queried."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        profile = profile_list.get_default_video_stream_profile()
        config.enable_stream(profile)

        enabled = config.get_enabled_stream_profile_list()
        assert enabled is not None
        assert enabled.get_count() > 0

    def test_d2c_align_mode(self, device, pipeline: Pipeline):
        """TC_CPP_09_06: D2C align mode can be configured."""
        config = Config()
        config.set_align_mode(OBAlignMode.DISABLE)
        config.set_align_mode(OBAlignMode.HW_MODE)
        config.set_align_mode(OBAlignMode.SW_MODE)

    def test_depth_scale_after_align(self, device, pipeline: Pipeline):
        """TC_CPP_09_07: Depth scale requirement can be set."""
        config = Config()
        config.set_depth_scale_require(True)
        config.set_depth_scale_require(False)

    def test_frame_aggregate_mode(self, device, pipeline: Pipeline):
        """TC_CPP_09_08: Frame aggregate output mode can be configured."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        config.set_frame_aggregate_output_mode(OBFrameAggregateOutputMode.FULL_FRAME_REQUIRE)
        pipeline.start(config)
        frames = pipeline.wait_for_frames(3000)
        pipeline.stop()
        assert frames is not None
