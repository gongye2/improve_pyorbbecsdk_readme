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
Hardware test: Depth Work Mode expanded (TC_CPP_15).

Ported from C++ hw_full_test.cpp:
  TC_CPP_15_02 enum_modes
  TC_CPP_15_03 switch_by_name
  TC_CPP_15_04 switch_by_struct
  TC_CPP_15_05 profile_change_after_switch
"""

import pytest

from pyorbbecsdk import (
    Config,
    Device,
    OBDepthWorkModeTag,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_15_DepthMode_Expanded:
    """Tests for depth work mode operations."""

    def test_enum_modes(self, device: Device):
        """TC_CPP_15_02: Depth work mode list can be enumerated."""
        mode_list = device.get_depth_work_mode_list()
        assert mode_list is not None

        count = mode_list.get_count()
        assert count > 0, "No depth work modes available"

        for i in range(count):
            mode = mode_list.get_depth_work_mode_by_index(i)
            assert mode is not None
            assert mode.name is not None
            assert len(mode.name) > 0
            # Tag should be a valid enum
            assert mode.tag in [
                OBDepthWorkModeTag.OB_DEVICE_DEPTH_WORK_MODE,
                OBDepthWorkModeTag.OB_CUSTOM_DEPTH_WORK_MODE,
            ]

    def test_switch_by_name(self, device: Device):
        """TC_CPP_15_03: Depth work mode can be switched by name."""
        mode_list = device.get_depth_work_mode_list()
        count = mode_list.get_count()
        if count < 2:
            pytest.skip("Only one depth work mode available")

        # Get current mode
        current = device.get_depth_work_mode()
        original_name = current.name

        # Find a different mode to switch to
        target_mode = None
        for i in range(count):
            mode = mode_list.get_depth_work_mode_by_index(i)
            if mode.name != original_name:
                target_mode = mode
                break

        assert target_mode is not None

        # Switch to target mode
        device.set_depth_work_mode(target_mode.name)
        new_mode = device.get_depth_work_mode()
        assert new_mode.name == target_mode.name

        # Restore original mode
        device.set_depth_work_mode(original_name)
        restored = device.get_depth_work_mode()
        assert restored.name == original_name

    def test_switch_by_struct(self, device: Device):
        """TC_CPP_15_04: Depth work mode can be switched via mode struct."""
        mode_list = device.get_depth_work_mode_list()
        count = mode_list.get_count()
        if count < 2:
            pytest.skip("Only one depth work mode available")

        current = device.get_depth_work_mode()

        # Switch using the mode struct directly
        target = mode_list.get_depth_work_mode_by_index(0)
        if target.name == current.name and count > 1:
            target = mode_list.get_depth_work_mode_by_index(1)

        device.set_depth_work_mode(target)
        new_mode = device.get_depth_work_mode()
        assert new_mode.name == target.name

        # Restore
        device.set_depth_work_mode(current)

    def test_profile_change_after_switch(self, device: Device, pipeline: Pipeline):
        """TC_CPP_15_05: Depth stream profiles remain valid after mode switch."""
        # Get current mode
        current_mode = device.get_depth_work_mode()

        mode_list = device.get_depth_work_mode_list()
        count = mode_list.get_count()

        if count < 2:
            pytest.skip("Only one depth work mode available")

        # Switch to a different mode
        target = None
        for i in range(count):
            mode = mode_list.get_depth_work_mode_by_index(i)
            if mode.name != current_mode.name:
                target = mode
                break

        assert target is not None
        device.set_depth_work_mode(target.name)

        # Verify depth stream still works
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        frames = pipeline.wait_for_frames(3000)
        pipeline.stop()
        assert frames is not None

        depth = frames.get_depth_frame()
        assert depth is not None
        assert depth.get_width() > 0
        assert depth.get_height() > 0

        # Restore original mode
        device.set_depth_work_mode(current_mode.name)
