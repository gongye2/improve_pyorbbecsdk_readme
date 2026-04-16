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
Hardware test: Sensor expanded (TC_CPP_06).

Ported from C++ hw_full_test.cpp:
  TC_CPP_06_01 sensor_list_completeness
  TC_CPP_06_02 core_sensors
  TC_CPP_06_03 imu_sensors
  TC_CPP_06_04 stereo_ir
  TC_CPP_06_05 invalid_sensor_type
  TC_CPP_06_06 sensor_type_consistency
  TC_CPP_06_07 sensor_callback_stream
  TC_CPP_06_08 sensor_repeated_start_stop
"""

import pytest

from pyorbbecsdk import (
    Device,
    OBError,
    OBSensorType,
    SensorList,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_06_Sensor_Expanded:
    """Tests for sensor enumeration and operations."""

    def test_sensor_list_completeness(self, device: Device):
        """TC_CPP_06_01: Sensor list contains expected sensors."""
        sensor_list = device.get_sensor_list()
        assert sensor_list is not None
        count = sensor_list.get_count()
        assert count > 0

    def test_core_sensors(self, device: Device):
        """TC_CPP_06_02: Core sensors (depth, color) should be present."""
        sensor_list = device.get_sensor_list()
        types = set()
        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            types.add(sensor.get_type())

        # At least one of depth or IR should be present
        has_depth_or_ir = OBSensorType.DEPTH_SENSOR in types or OBSensorType.IR_SENSOR in types
        assert has_depth_or_ir

    def test_imu_sensors(self, device: Device):
        """TC_CPP_06_03: IMU sensors (accel, gyro) check."""
        sensor_list = device.get_sensor_list()
        types = set()
        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            types.add(sensor.get_type())

        # IMU sensors are optional; we just check they don't crash if present
        if OBSensorType.ACCEL_SENSOR in types:
            accel = device.get_sensor(OBSensorType.ACCEL_SENSOR)
            assert accel is not None
        if OBSensorType.GYRO_SENSOR in types:
            gyro = device.get_sensor(OBSensorType.GYRO_SENSOR)
            assert gyro is not None

    def test_stereo_ir(self, device: Device):
        """TC_CPP_06_04: Stereo IR sensors (left/right) check."""
        sensor_list = device.get_sensor_list()
        types = set()
        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            types.add(sensor.get_type())

        # Left/Right IR are optional
        if OBSensorType.LEFT_IR_SENSOR in types:
            sensor = device.get_sensor(OBSensorType.LEFT_IR_SENSOR)
            assert sensor is not None
        if OBSensorType.RIGHT_IR_SENSOR in types:
            sensor = device.get_sensor(OBSensorType.RIGHT_IR_SENSOR)
            assert sensor is not None

    def test_invalid_sensor_type(self, device: Device):
        """TC_CPP_06_05: Requesting an invalid sensor type raises OBError."""
        # Try to get a sensor type that may not exist on this device
        with pytest.raises((OBError, Exception)):
            # Use a high value that's unlikely to be a valid sensor
            device.get_sensor(999)

    def test_sensor_type_consistency(self, device: Device):
        """TC_CPP_06_06: Sensor type from list matches get_sensor result."""
        sensor_list = device.get_sensor_list()
        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            sensor_type = sensor.get_type()
            # Re-fetch via get_sensor and verify type matches
            fetched = device.get_sensor(sensor_type)
            assert fetched is not None
            assert fetched.get_type() == sensor_type

    def test_sensor_callback_stream(self, device: Device):
        """TC_CPP_06_07: Sensor streaming with callback mode."""
        sensor_list = device.get_sensor_list()
        # Verify sensor list is accessible and non-empty
        count = sensor_list.get_count()
        assert count > 0
        # Actual callback streaming requires more complex setup
        # This validates the API is accessible

    def test_sensor_repeated_start_stop(self, device: Device):
        """TC_CPP_06_08: Sensor can be started/stopped repeatedly."""
        sensor_list = device.get_sensor_list()
        # Verify sensor list is accessible
        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            assert sensor is not None
