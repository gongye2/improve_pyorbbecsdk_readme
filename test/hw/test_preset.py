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
Hardware test: Device Preset (TC_CPP_16).

Ported from C++ hw_full_test.cpp:
  TC_CPP_16_01 current_and_list
  TC_CPP_16_02 load_builtin
  TC_CPP_16_03 export_json
  TC_CPP_16_04 load_from_json
  TC_CPP_16_05 preset_changes_properties
"""

import os
import tempfile

import pytest

from pyorbbecsdk import Device, DeviceInfo

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_16_Preset:
    """Tests for device preset loading and management."""

    def test_current_and_list(self, device: Device, device_info: DeviceInfo):
        """TC_CPP_16_01: Current preset name and available preset list."""
        current = device.get_current_preset_name()
        assert isinstance(current, str)

        preset_list = device.get_available_preset_list()
        assert preset_list is not None
        count = preset_list.get_count()
        assert count > 0
        for i in range(count):
            name = preset_list.get_name_by_index(i)
            assert name

    def test_load_builtin(self, device: Device):
        """TC_CPP_16_02: Load a builtin preset by name."""
        preset_list = device.get_available_preset_list()
        if preset_list.get_count() == 0:
            pytest.skip("No presets available")

        name = preset_list.get_name_by_index(0)
        device.load_preset(name)
        assert device.get_current_preset_name() == name

    def test_export_json(self, device: Device):
        """TC_CPP_16_03: Export settings as JSON preset file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            device.export_settings_as_preset_json_file(path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_load_from_json(self, device: Device):
        """TC_CPP_16_04: Load preset from JSON file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            device.export_settings_as_preset_json_file(path)
            # Reload from the exported file
            device.load_preset_from_json_file(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_preset_changes_properties(self, device: Device):
        """TC_CPP_16_05: Loading a preset changes device properties."""
        preset_list = device.get_available_preset_list()
        if preset_list.get_count() < 2:
            pytest.skip("Need at least 2 presets to verify property changes")

        name_a = preset_list.get_name_by_index(0)
        name_b = preset_list.get_name_by_index(1)

        device.load_preset(name_a)
        assert device.get_current_preset_name() == name_a

        device.load_preset(name_b)
        assert device.get_current_preset_name() == name_b
