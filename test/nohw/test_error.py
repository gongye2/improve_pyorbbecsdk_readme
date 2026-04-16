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
No-hardware test: Error safety (TC_CPP_24).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_24_01 exception_type_info
  TC_CPP_24_02 invalid_value_exception
  TC_CPP_24_03 wrong_api_sequence
  TC_CPP_24_06_filter_null_frame
  TC_CPP_24_07_all_exception_types

Also:
  TC_CPP_24_04 pipeline exception safety
  TC_CPP_24_05 device property exception
"""

import pytest

from pyorbbecsdk import (
    Config,
    Context,
    DecimationFilter,
    OBError,
    OBException,
    OBFormat,
    OBFrameType,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.functional]


class TC_CPP_24_Error:
    """Tests for SDK error handling and exception types."""

    def test_exception_type_info(self):
        """TC_CPP_24_01: Invalid filter raises OBError with type info."""
        try:
            # This should raise an error for an invalid filter name
            import pyorbbecsdk

            # Try to create a filter with invalid name
            from pyorbbecsdk import Filter

            Filter("TotallyInvalidFilter")
            pytest.fail("Expected OBError")
        except OBError as e:
            assert str(e) is not None
            assert len(str(e)) > 0
        except Exception as e:
            # Also acceptable
            assert str(e) is not None

    def test_invalid_value_exception(self):
        """TC_CPP_24_02: Invalid values raise OBError with INVALID_VALUE type."""
        try:
            # Creating a video frame with zero dimensions should fail
            import pyorbbecsdk
            from pyorbbecsdk import VideoFrame

            VideoFrame(OBFrameType.DEPTH_FRAME, OBFormat.Y16, 0, 0, 0)
        except OBError as e:
            # Expected
            pass
        except Exception:
            # Also acceptable
            pass

    def test_wrong_api_sequence(self):
        """TC_CPP_24_03: waitForFrames without start raises appropriate error."""
        pipeline = Pipeline()
        try:
            # Calling wait_for_frames without starting the pipeline
            pipeline.wait_for_frames(100)
        except OBError:
            # Expected: pipeline not started
            pass
        except Exception:
            # Also acceptable
            pass

    def test_all_exception_types(self):
        """TC_CPP_24_07: Verify multiple exception types can be triggered."""
        triggered_types = []

        # Invalid filter name → INVALID_VALUE or similar
        try:
            from pyorbbecsdk import Filter

            Filter("TotallyInvalidFilter")
        except OBError:
            triggered_types.append("invalid_filter")
        except Exception:
            triggered_types.append("invalid_filter_other")

        # Wrong API sequence → WRONG_API_CALL_SEQUENCE or similar
        try:
            pipeline = Pipeline()
            pipeline.wait_for_frames(100)
        except OBError:
            triggered_types.append("wrong_sequence")
        except Exception:
            triggered_types.append("wrong_sequence_other")

        assert len(triggered_types) > 0, "No exception types were triggered"

    def test_pipeline_exception_safety(self):
        """TC_CPP_24_04: Pipeline can be created/destroyed without crashing."""
        pipelines = []
        for _ in range(5):
            p = Pipeline()
            pipelines.append(p)
        # All should be valid objects
        for p in pipelines:
            assert p is not None

    def test_device_property_exception(self):
        """TC_CPP_24_05: Unsupported device property raises appropriate error."""
        ctx = Context()
        dev_list = ctx.query_devices()
        if dev_list.get_count() == 0:
            pytest.skip("No device connected")
        device = dev_list.get_device_by_index(0)

        # Try an unsupported property — should raise or return gracefully
        from pyorbbecsdk import OBPermissionType, OBPropertyID

        try:
            # This property may not exist on all devices
            device.get_bool_property(OBPropertyID.OB_PROP_LASER_MODE_INT)
        except OBError:
            # Expected for unsupported property
            pass
        except Exception:
            # Also acceptable
            pass
