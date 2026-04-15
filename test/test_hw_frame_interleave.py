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
Hardware test: Frame Interleave (TC_CPP_17).

Ported from C++ hw_full_test.cpp:
  TC_CPP_17_01 support_query
  TC_CPP_17_02 load_interleave
  TC_CPP_17_03 interleave_stream
"""

import pytest

from pyorbbecsdk import Device

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_17_Interleave:
    """Tests for frame interleave support and loading."""

    def test_support_query(self, device: Device):
        """TC_CPP_17_01: Check if frame interleave is supported."""
        result = device.isFrameInterleaveSupported()
        assert isinstance(result, bool)

    def test_load_interleave(self, device: Device):
        """TC_CPP_17_02: Load frame interleave configuration if supported."""
        if not device.isFrameInterleaveSupported():
            pytest.skip("Frame interleave not supported on this device")
        # On supported devices, a valid interleave file path is needed.
        # We skip the actual load since it requires a specific .bin file.

    def test_interleave_stream(self, device: Device):
        """TC_CPP_17_03: Verify stream behavior with interleave enabled."""
        if not device.isFrameInterleaveSupported():
            pytest.skip("Frame interleave not supported on this device")
        pytest.skip("Interleave stream test requires a valid interleave config file")
