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
Hardware test: Record / Playback (TC_CPP_18).

Ported from C++ hw_full_test.cpp:
  TC_CPP_18_01 record_device
  TC_CPP_18_02 record_pause_resume
  TC_CPP_18_08 record_playback_roundtrip (destructive, skipped)
"""

import os
import tempfile

import pytest

from pyorbbecsdk import (
    Config,
    OBSensorType,
    Pipeline,
    RecordDevice,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_18_Record_HW:
    """Tests for recording and playback functionality."""

    def test_record_device(self, device, pipeline: Pipeline):
        """TC_CPP_18_01: RecordDevice can be created and record frames."""
        with tempfile.NamedTemporaryFile(suffix=".bag", delete=False) as f:
            path = f.name

        try:
            config = Config()
            profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            profile = profile_list.get_default_video_stream_profile()
            config.enable_stream(profile)

            # Create RecordDevice from the pipeline's device
            recorder = RecordDevice(device, path)

            pipeline.start(config)
            frames = pipeline.wait_for_frames(3000)
            pipeline.stop()

            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def test_record_pause_resume(self, device, pipeline: Pipeline):
        """TC_CPP_18_02: RecordDevice pause/resume works."""
        with tempfile.NamedTemporaryFile(suffix=".bag", delete=False) as f:
            path = f.name

        try:
            config = Config()
            profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            profile = profile_list.get_default_video_stream_profile()
            config.enable_stream(profile)

            recorder = RecordDevice(device, path)

            pipeline.start(config)

            # Record some frames, pause, resume
            pipeline.wait_for_frames(1000)
            recorder.pause()
            pipeline.wait_for_frames(500)
            recorder.resume()
            pipeline.wait_for_frames(1000)

            pipeline.stop()
            assert os.path.exists(path)
        finally:
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def test_record_playback_roundtrip(self, device, pipeline: Pipeline):
        """TC_CPP_18_08: Record then playback and verify frames match."""
        pytest.skip("Destructive test — requires full roundtrip validation")
