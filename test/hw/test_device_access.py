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
Hardware test: Device Access Mode (TC_CPP_05).

Ported from C++ hw_full_test.cpp:
  TC_CPP_05_01 default_access
  TC_CPP_05_02 exclusive_access
  TC_CPP_05_03 shared_access
  TC_CPP_05_04 control_only_access
"""

import pytest

from pyorbbecsdk import (
    Context,
    OBDeviceAccessMode,
    OBPermissionType,
    OBPropertyID,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_05_AccessMode:
    """Tests for device access mode handling."""

    def test_default_access(self, context: Context, device):
        """TC_CPP_05_01: Default access mode should allow basic operations."""
        info = device.get_device_info()
        assert info is not None
        assert info.get_name()
        # Default access allows property reads
        device.is_property_supported(
            OBPropertyID.OB_PROP_DEPTH_AUTO_EXPOSURE_BOOL,
            OBPermissionType.PERMISSION_READ_WRITE,
        )

    def test_exclusive_access(self, context: Context, device_info):
        """TC_CPP_05_02: Exclusive access via DeviceList."""
        sn = device_info.get_serial_number()
        dev_list = context.query_devices()
        count = dev_list.get_count()
        if count == 0:
            pytest.skip("No device connected")
        # Exclusive access should succeed when no other holder
        dev = dev_list.get_device_by_index(0, OBDeviceAccessMode.OB_DEVICE_EXCLUSIVE_ACCESS)
        assert dev is not None
        info = dev.get_device_info()
        assert info.get_serial_number() == sn

    def test_shared_access(self, context: Context, device_info):
        """TC_CPP_05_03: Shared (default) access should always succeed."""
        dev_list = context.query_devices()
        count = dev_list.get_count()
        if count == 0:
            pytest.skip("No device connected")
        dev = dev_list.get_device_by_index(0, OBDeviceAccessMode.OB_DEVICE_DEFAULT_ACCESS)
        assert dev is not None
        info = dev.get_device_info()
        assert info.get_serial_number() == device_info.get_serial_number()

    def test_control_only_access(self, context: Context, device_info):
        """TC_CPP_05_04: Control-only access allows property operations."""
        dev_list = context.query_devices()
        count = dev_list.get_count()
        if count == 0:
            pytest.skip("No device connected")
        dev = dev_list.get_device_by_index(0, OBDeviceAccessMode.OB_DEVICE_CONTROL_ACCESS)
        assert dev is not None
        info = dev.get_device_info()
        assert info.get_serial_number() == device_info.get_serial_number()
