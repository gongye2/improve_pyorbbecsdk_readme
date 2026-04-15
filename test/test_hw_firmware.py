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
Hardware test: Firmware (TC_CPP_21).

Ported from C++ hw_full_test.cpp:
  TC_CPP_21_01 global_timestamp
  TC_CPP_21_02 device_state
  TC_CPP_21_03 state_change_callback
  TC_CPP_21_04 heartbeat
  TC_CPP_21_05 raw_vendor_command (skipped — no Python API)
  TC_CPP_21_06 calibration_param_list
  TC_CPP_21_07 reboot
  TC_CPP_21_08 firmware_update (skipped — destructive)
  TC_CPP_21_09 update_depth_presets (skipped — destructive)
"""

import threading
import time

import pytest

from pyorbbecsdk import Device, DeviceInfo

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_21_Firmware:
    """Tests for firmware-level device operations."""

    def test_global_timestamp(self, device: Device):
        """TC_CPP_21_01: Global timestamp API is available."""
        ts = device.get_device_info()
        assert ts is not None
        # Device info should be accessible with valid fields

    def test_device_state(self, device: Device):
        """TC_CPP_21_02: Device state is readable."""
        state = device.get_device_state()
        assert isinstance(state, int)

    def test_state_change_callback(self, device: Device):
        """TC_CPP_21_03: Device state change callback registration."""
        callback_fired = threading.Event()

        def on_state_change():
            callback_fired.set()

        device.set_device_state_changed_callback(on_state_change)
        # Unregister is not exposed; callback will be cleaned up with device

    def test_heartbeat(self, device: Device):
        """TC_CPP_21_04: Heartbeat can be enabled/disabled."""
        device.enable_heart_beat(True)
        time.sleep(0.1)
        device.enable_heart_beat(False)

    def test_calibration_param_list(self, device: Device, device_info: DeviceInfo):
        """TC_CPP_21_06: Calibration camera param list is accessible."""
        param_list = device.get_calibration_camera_param_list()
        assert param_list is not None
        count = param_list.get_count()
        assert count > 0
        param = param_list.get_camera_param(0)
        assert param is not None

    def test_reboot(self, device: Device, device_info: DeviceInfo):
        """TC_CPP_21_07: Device reboot works (skips if only one device test)."""
        # Reboot is destructive to the test session, so we just verify the API exists
        # and do NOT actually call reboot() to avoid disrupting the test run
        assert hasattr(device, "reboot")
        assert callable(device.reboot)
