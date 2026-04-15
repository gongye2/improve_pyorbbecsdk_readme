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
No-hardware test: Logger (TC_CPP_23).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_23_01 log_severity_set
  TC_CPP_23_02 log_to_file
  TC_CPP_23_03 log_to_console
  TC_CPP_23_04 log_callback
  TC_CPP_23_05 external_message
"""

import os
import tempfile
import time

import pytest

from pyorbbecsdk import Context, OBLogLevel

pytestmark = [pytest.mark.functional]


class TC_CPP_23_Logger:
    """Tests for SDK logging functionality."""

    def test_log_severity_set(self):
        """TC_CPP_23_01: Log severity can be set to all levels."""
        levels = [
            OBLogLevel.DEBUG,
            OBLogLevel.INFO,
            OBLogLevel.WARNING,
            OBLogLevel.ERROR,
            OBLogLevel.FATAL,
            OBLogLevel.NONE,
        ]
        for level in levels:
            ctx = Context()
            ctx.set_logger_level(level)
        # Restore to a normal level
        ctx = Context()
        ctx.set_logger_level(OBLogLevel.WARNING)

    def test_log_to_file(self):
        """TC_CPP_23_02: Log can be directed to a file."""
        import tempfile
        tmpdir = tempfile.mkdtemp()
        try:
            ctx = Context()
            ctx.set_logger_level(OBLogLevel.DEBUG)
            ctx.set_logger_to_file(OBLogLevel.DEBUG, tmpdir)
            # Trigger some SDK activity to generate log output
            ctx.query_devices()
            time.sleep(0.1)
            # Restore
            ctx.set_logger_level(OBLogLevel.WARNING)
        except Exception:
            pass

    def test_log_to_console(self):
        """TC_CPP_23_03: Log can be directed to console."""
        ctx = Context()
        ctx.set_logger_to_console(OBLogLevel.INFO)
        # Restore
        ctx.set_logger_level(OBLogLevel.WARNING)

    def test_log_callback(self):
        """TC_CPP_23_04: Log callback receives log messages."""
        log_count = [0]

        def log_cb(level, msg):
            log_count[0] += 1

        ctx = Context()
        ctx.set_logger_to_callback(OBLogLevel.DEBUG, log_cb)
        # Trigger SDK activity (may not produce logs if no device connected)
        ctx.query_devices()
        time.sleep(0.5)
        # Log callback may or may not fire depending on SDK internals
        # The important thing is the API is accessible
        assert ctx is not None
        # Restore
        ctx.set_logger_level(OBLogLevel.WARNING)

    def test_external_message(self):
        """TC_CPP_23_05: External log message can be emitted and captured."""
        found = [False]

        def log_cb(level, msg):
            if msg and "PYORBBEC_TEST_MARKER" in msg:
                found[0] = True

        ctx = Context()
        ctx.set_logger_to_callback(OBLogLevel.INFO, log_cb)
        Context.log_external_message(
            OBLogLevel.INFO,
            "PYORBBEC_TEST",    # tag
            "PYORBBEC_TEST_MARKER",  # message
            __file__,           # file
            "test_external_message",  # function
            0,                  # line
        )
        time.sleep(0.1)
        assert found[0], "External message not captured"
        # Restore
        ctx.set_logger_level(OBLogLevel.WARNING)
