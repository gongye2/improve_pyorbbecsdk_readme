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
No-hardware test: Data structures (TC_CPP_25).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_25_05 config_mode_structs
  TC_CPP_25_06_hdr_roi_point_imu_structs
  TC_CPP_25_07_property_range_structs
"""

import numpy as np
import pytest

from pyorbbecsdk import (
    OBAccelValue,
    OBDepthWorkMode,
    OBFilterConfigSchemaItem,
    OBFloatPropertyRange,
    OBHdrConfig,
    OBIntPropertyRange,
    OBMultiDeviceSyncConfig,
    OBMultiDeviceSyncMode,
    OBPoint3f,
    OBRegionOfInterest,
)

pytestmark = [pytest.mark.functional]


class TC_CPP_25_DataStruct:
    """Tests for SDK data structures."""

    def test_config_mode_structs(self):
        """TC_CPP_25_05: Config mode structs can be created and populated."""
        # OBDepthWorkMode
        mode = OBDepthWorkMode()
        assert mode is not None

        # OBMultiDeviceSyncConfig
        sync_config = OBMultiDeviceSyncConfig()
        assert sync_config is not None
        sync_config.mode = OBMultiDeviceSyncMode.FREE_RUN
        assert sync_config.mode == OBMultiDeviceSyncMode.FREE_RUN

    def test_hdr_roi_point_imu_structs(self):
        """TC_CPP_25_06: HDR, ROI, Point, and IMU structs work correctly."""
        # OBHdrConfig
        hdr = OBHdrConfig()
        hdr.enable = 1
        assert hdr.enable == 1

        # OBRegionOfInterest
        roi = OBRegionOfInterest()
        roi.x0_left = 0
        roi.y0_top = 0
        roi.x1_right = 640
        roi.y1_bottom = 480
        assert roi.x1_right == 640

        # OBPoint3f
        p = OBPoint3f()
        p.x = 1.0
        p.y = 2.0
        p.z = 3.0
        assert abs(p.z - 3.0) < 1e-6

        # OBAccelValue
        accel = OBAccelValue()
        accel.x = 0.0
        accel.y = 0.0
        accel.z = 9.8
        assert abs(accel.z - 9.8) < 0.01

    def test_property_range_structs(self):
        """TC_CPP_25_07: Property range structs can be created and populated."""
        # OBIntPropertyRange
        int_range = OBIntPropertyRange()
        int_range.min = 0
        int_range.max = 100
        int_range.step = 1
        int_range.current = 50
        int_range.default_value = 50
        assert int_range.max > int_range.min
        assert int_range.current >= int_range.min
        assert int_range.current <= int_range.max

        # OBFloatPropertyRange
        float_range = OBFloatPropertyRange()
        float_range.min = 0.0
        float_range.max = 1.0
        float_range.step = 0.1
        float_range.current = 0.5
        float_range.default_value = 0.5
        assert float_range.max > float_range.min

        # OBFilterConfigSchemaItem
        item = OBFilterConfigSchemaItem()
        assert item is not None
