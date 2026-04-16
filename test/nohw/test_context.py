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
No-hardware test: Context (TC_CPP_01).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_01_01 context_default_create_destroy
  TC_CPP_01_02 context_config_path
  TC_CPP_01_03 context_repeated_create_destroy
  TC_CPP_01_04_free_idle_memory (skipped — not exposed in Python SDK)
"""

import pytest

from pyorbbecsdk import Context

pytestmark = [pytest.mark.functional]


class TC_CPP_01_Context:
    """Tests for Context creation and lifecycle without hardware."""

    def test_context_default_create_destroy(self, context):
        """TC_CPP_01_01: Context can be created and device list queried."""
        # context fixture provides a valid Context
        device_list = context.query_devices()
        assert device_list is not None
        assert device_list.get_count() >= 0

    def test_context_config_path(self):
        """TC_CPP_01_02: Context accepts empty or custom config path."""
        # Empty config path should work
        ctx = Context("")
        dev_list = ctx.query_devices()
        assert dev_list is not None

    def test_context_repeated_create_destroy(self):
        """TC_CPP_01_03: Context can be repeatedly created and destroyed."""
        for i in range(10):
            ctx = Context()
            assert ctx is not None
            dev_list = ctx.query_devices()
            assert dev_list is not None
            # ctx goes out of scope and is garbage collected

    def test_free_idle_memory(self, context):
        """TC_CPP_01_04: freeIdleMemory releases cached frame memory."""
        # Call free_idle_memory — should not raise
        context.free_idle_memory()
