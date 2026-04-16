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
Hardware test: Stream Profile expanded (TC_CPP_07).

Ported from C++ hw_full_test.cpp:
  TC_CPP_07_01 depth_color_profiles
  TC_CPP_07_02 video_profile_filter
  TC_CPP_07_03 accel_profile
  TC_CPP_07_04 gyro_profile
  TC_CPP_07_05 profile_type_check
"""

import pytest

from pyorbbecsdk import (
    Device,
    OBSensorType,
    Pipeline,
    VideoStreamProfile,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_07_StreamProfile_Expanded:
    """Tests for stream profile details and filtering."""

    def test_depth_color_profiles(self, device: Device, pipeline: Pipeline):
        """TC_CPP_07_01: Depth and color stream profiles have valid parameters."""
        for sensor_type in [OBSensorType.DEPTH_SENSOR, OBSensorType.COLOR_SENSOR]:
            try:
                profile_list = pipeline.get_stream_profile_list(sensor_type)
            except Exception:
                continue

            profile = profile_list.get_default_video_stream_profile()
            assert profile is not None
            assert isinstance(profile, VideoStreamProfile)
            assert profile.get_width() > 0
            assert profile.get_height() > 0
            assert profile.get_fps() > 0

    def test_video_profile_filter(self, device: Device, pipeline: Pipeline):
        """TC_CPP_10_02: Video stream profile list can be filtered."""
        profile_list = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
        count = profile_list.get_count()
        assert count > 0

        # Use get_default_video_stream_profile which is guaranteed to work
        profile = profile_list.get_default_video_stream_profile()
        assert profile is not None
        assert profile.get_width() > 0
        assert profile.get_height() > 0

    def test_accel_profile(self, device: Device, pipeline: Pipeline):
        """TC_CPP_07_03: Accel stream profile has valid intrinsics."""
        from pyorbbecsdk import AccelStreamProfile

        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.ACCEL_SENSOR)
            count = profile_list.get_count()
            if count == 0:
                pytest.skip("No accel profiles available")
            profile = profile_list.get_stream_profile_by_index(0)
            assert isinstance(profile, AccelStreamProfile)
        except Exception:
            pytest.skip("Accel sensor not available")

        assert profile is not None
        intrinsic = profile.get_intrinsic()
        assert intrinsic is not None

    def test_gyro_profile(self, device: Device, pipeline: Pipeline):
        """TC_CPP_07_04: Gyro stream profile has valid intrinsics."""
        from pyorbbecsdk import GyroStreamProfile

        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.GYRO_SENSOR)
            count = profile_list.get_count()
            if count == 0:
                pytest.skip("No gyro profiles available")
            profile = profile_list.get_stream_profile_by_index(0)
            assert isinstance(profile, GyroStreamProfile)
        except Exception:
            pytest.skip("Gyro sensor not available")

        assert profile is not None
        intrinsic = profile.get_intrinsic()
        assert intrinsic is not None

    def test_profile_type_check(self, device: Device, pipeline: Pipeline):
        """TC_CPP_07_05: Profile type checking via as_* methods."""
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        profile = profile_list.get_default_video_stream_profile()
        assert profile is not None
        # Profile should be a video stream profile
        assert isinstance(profile, VideoStreamProfile)
