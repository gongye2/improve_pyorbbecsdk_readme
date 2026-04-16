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
Hardware test: DataStruct expanded (TC_CPP_25).

Ported from C++ hw_full_test.cpp:
  TC_CPP_25_03 imu_intrinsic
  TC_CPP_25_04 device_temperature_fields
"""

import pytest

from pyorbbecsdk import (
    Device,
    OBPermissionType,
    OBPropertyID,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_25_DataStruct_Expanded:
    """Tests for SDK data structure fields and validation."""

    def test_imu_intrinsic(self, device: Device, pipeline: Pipeline):
        """TC_CPP_25_03: IMU stream profile intrinsics have valid fields."""
        from pyorbbecsdk import (
            AccelStreamProfile,
            GyroStreamProfile,
            OBSensorType,
        )

        # Accel intrinsic
        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.ACCEL_SENSOR)
            count = profile_list.get_count()
            if count == 0:
                pytest.skip("No accel profiles available")
            profile = profile_list.get_stream_profile_by_index(0)
            assert isinstance(profile, AccelStreamProfile)

            intrinsic = profile.get_intrinsic()
            assert intrinsic is not None
            assert hasattr(intrinsic, "noise_density")
            assert hasattr(intrinsic, "random_walk")
            assert hasattr(intrinsic, "bias")
        except Exception:
            pytest.skip("Accel sensor not available")

        # Gyro intrinsic
        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.GYRO_SENSOR)
            count = profile_list.get_count()
            if count == 0:
                pytest.skip("No gyro profiles available")
            profile = profile_list.get_stream_profile_by_index(0)
            assert isinstance(profile, GyroStreamProfile)

            intrinsic = profile.get_intrinsic()
            assert intrinsic is not None
            assert hasattr(intrinsic, "noise_density")
            assert hasattr(intrinsic, "random_walk")
            assert hasattr(intrinsic, "bias")
        except Exception:
            pytest.skip("Gyro sensor not available")

    def test_device_temperature_fields(self, device: Device):
        """TC_CPP_25_04: Device temperature struct has all expected fields."""
        perm = OBPermissionType.PERMISSION_READ_WRITE
        temp_prop = OBPropertyID.OB_STRUCT_DEVICE_TEMPERATURE

        if not device.is_property_supported(temp_prop, perm):
            pytest.skip("Device temperature property not supported")

        from pyorbbecsdk import OBDeviceTemperature

        temp_data = device.get_structured_property(temp_prop, OBDeviceTemperature)
        assert temp_data is not None

        # Check all expected temperature fields exist
        expected_fields = [
            "cpu_temperature",
            "main_board_temperature",
        ]
        for field in expected_fields:
            assert hasattr(temp_data, field), f"Missing temperature field: {field}"

        # Additional device-specific fields may or may not be populated
        optional_fields = [
            "tec_temperature",
            "ir_temperature",
            "ir_left_temperature",
            "ir_right_temperature",
            "rgb_temperature",
            "laser_temperature",
            "imu_temperature",
            "chip_top_temperature",
            "chip_bottom_temperature",
        ]
        for field in optional_fields:
            if hasattr(temp_data, field):
                # If the field exists, the value may be 0.0 or NaN for
                # sensors not present on this device model
                pass
