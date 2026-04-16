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
Hardware test: Error safety (TC_CPP_24).

Ported from C++ hw_full_test.cpp:
  TC_CPP_24_04 pipeline_exception_safety
  TC_CPP_24_05 device_property_exception
"""

import pytest

from pyorbbecsdk import (
    Config,
    Device,
    OBError,
    OBPermissionType,
    OBPropertyID,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_24_Error_Safety:
    """Tests for error handling and exception safety."""

    def test_pipeline_exception_safety(self, device: Device, pipeline: Pipeline):
        """TC_CPP_24_04: Pipeline operations are exception-safe."""
        # Start a valid stream
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        # Wait for a frame
        frames = pipeline.wait_for_frames(3000)
        assert frames is not None

        # Stop should be safe even after error conditions
        pipeline.stop()

        # Double stop should be safe
        pipeline.stop()

        # Starting with an empty config should raise but not crash
        bad_config = Config()
        try:
            pipeline.start(bad_config)
            pipeline.stop()
        except (OBError, Exception):
            pipeline.stop()

    def test_device_property_exception(self, device: Device):
        """TC_CPP_24_05: Device property errors raise OBError, not crash."""
        perm = OBPermissionType.PERMISSION_READ_WRITE

        # Reading an unsupported property should raise OBError
        prop = OBPropertyID.OB_DEVICE_PTP_CLOCK_SYNC_ENABLE_BOOL
        if not device.is_property_supported(prop, perm):
            with pytest.raises(OBError):
                device.get_bool_property(prop)

        # Invalid sensor index should raise OBError
        sensor_list = device.get_sensor_list()
        count = sensor_list.get_count()
        with pytest.raises(OBError):
            sensor_list.get_sensor_by_index(999)

    def test_filter_null_frame(self, device, pipeline: Pipeline):
        """TC_CPP_24_06: Filter rejects None/null frame safely."""
        from pyorbbecsdk import TemporalFilter

        # Collect a depth frame first to initialize the filter properly
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        config.enable_stream(profile_list.get_default_video_stream_profile())
        pipeline.start(config)

        frames = pipeline.wait_for_frames(3000)
        pipeline.stop()
        assert frames is not None

        filt = TemporalFilter()
        with pytest.raises((ValueError, TypeError)):
            filt.process(None)
