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
No-hardware test: Version (TC_CPP_22).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_22_01 full_version
  TC_CPP_22_02 major_minor_patch
  TC_CPP_22_03 stage_version
"""

import pytest

from pyorbbecsdk import get_version

pytestmark = [pytest.mark.functional]


class TC_CPP_22_Version:
    """Tests for SDK version information."""

    def test_full_version(self):
        """TC_CPP_22_01: SDK version string is non-empty."""
        version = get_version()
        assert version is not None
        assert len(version) > 0

    def test_version_components(self):
        """TC_CPP_22_02: Version can be parsed into major.minor.patch."""
        version = get_version()
        parts = version.split(".")
        # At minimum, expect major.minor.patch (e.g., "2.8.2")
        assert len(parts) >= 3
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        assert major >= 0
        assert minor >= 0
        assert patch >= 0
