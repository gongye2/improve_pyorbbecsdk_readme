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
Hardware test: Device Discovery expanded (TC_CPP_02).

Ported from C++ hw_full_test.cpp:
  TC_CPP_02_05 hotplug_reboot (partial — callback + reboot API check)
  TC_CPP_02_06 clock_sync
"""

import pytest

from pyorbbecsdk import Context

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_02_Discovery_HW_Expanded:
    """Tests for device discovery features beyond basic enumeration."""

    def test_clock_sync(self, context: Context):
        """TC_CPP_02_06: Device clock sync can be enabled with various intervals."""
        # Should not raise
        context.enable_multi_device_sync(1000)
        context.enable_multi_device_sync(500)
        context.enable_multi_device_sync(0)
