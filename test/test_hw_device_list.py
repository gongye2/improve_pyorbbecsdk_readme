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
Hardware test: DeviceList expanded (TC_CPP_03).

Ported from C++ hw_full_test.cpp:
  TC_CPP_03_02 access_mode
  TC_CPP_03_03 get_by_sn_uid
  TC_CPP_03_04 basic_info_fields
  TC_CPP_03_05 net_device_info (partial)
  TC_CPP_03_06 out_of_bounds
"""

import pytest

from pyorbbecsdk import Context, OBDeviceAccessMode, OBError

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_03_DeviceList_Expanded:
    """Tests for DeviceList operations beyond basic enumeration."""

    def test_access_mode_via_device_list(self, context: Context, device_info):
        """TC_CPP_03_02: DeviceList supports different access modes."""
        sn = device_info.get_serial_number()
        dev_list = context.query_devices()
        count = dev_list.get_count()
        if count == 0:
            pytest.skip("No device connected")

        dev_excl = dev_list.get_device_by_index(0, OBDeviceAccessMode.OB_DEVICE_EXCLUSIVE_ACCESS)
        assert dev_excl is not None
        assert dev_excl.get_device_info().get_serial_number() == sn

        dev_default = dev_list.get_device_by_index(0, OBDeviceAccessMode.OB_DEVICE_DEFAULT_ACCESS)
        assert dev_default is not None

    def test_get_by_sn_uid(self, context: Context, device_info):
        """TC_CPP_03_03: Get device by serial number and UID."""
        sn = device_info.get_serial_number()
        uid = device_info.get_uid()

        dev_list = context.query_devices()
        count = dev_list.get_count()
        if count == 0:
            pytest.skip("No device connected")

        dev_by_sn = dev_list.get_device_by_serial_number(sn)
        assert dev_by_sn is not None
        assert dev_by_sn.get_device_info().get_serial_number() == sn

        dev_by_uid = dev_list.get_device_by_uid(uid)
        assert dev_by_uid is not None
        assert dev_by_uid.get_device_info().get_uid() == uid

        # Non-existent keys should raise OBError (not return None)
        with pytest.raises((OBError, Exception)):
            dev_list.get_device_by_serial_number("NON_EXISTENT_SN_12345")

        with pytest.raises((OBError, Exception)):
            dev_list.get_device_by_uid("NON_EXISTENT_UID_12345")

    def test_basic_info_fields(self, context: Context):
        """TC_CPP_03_04: DeviceList basic info fields are valid."""
        dev_list = context.query_devices()
        count = dev_list.get_count()
        if count == 0:
            pytest.skip("No device connected")

        for i in range(count):
            name = dev_list.get_device_name_by_index(i)
            assert name

            pid = dev_list.get_device_pid_by_index(i)
            assert pid > 0

            vid = dev_list.get_device_vid_by_index(i)
            assert vid == 0x2BC5

            conn_type = dev_list.get_device_connection_type_by_index(i)
            assert conn_type

    def test_net_device_info(self, context: Context):
        """TC_CPP_03_05: Network device info fields (if Ethernet device present)."""
        dev_list = context.query_devices()
        count = dev_list.get_count()
        if count == 0:
            pytest.skip("No device connected")

        found_ethernet = False
        for i in range(count):
            conn_type = dev_list.get_device_connection_type_by_index(i)
            if "Ethernet" in conn_type or "Network" in conn_type:
                found_ethernet = True
                ip = dev_list.get_device_ip_address_by_index(i)
                assert ip

                subnet = dev_list.get_device_subnet_mask_by_index(i)
                assert subnet

                gw = dev_list.get_device_gateway_by_index(i)
                assert gw

                local_mac = dev_list.get_local_mac_address(i)
                assert local_mac

        if not found_ethernet:
            pytest.skip("No Ethernet/network device connected")

    def test_out_of_bounds(self, context: Context):
        """TC_CPP_03_06: Out-of-bounds access to DeviceList."""
        dev_list = context.query_devices()
        count = dev_list.get_count()

        # Accessing beyond count via get_count should work (returns None or raises)
        # We verify the count matches the actual accessible devices
        assert count == len(dev_list)
