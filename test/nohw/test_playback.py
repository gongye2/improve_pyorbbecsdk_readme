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
No-hardware test: Playback (TC_CPP_18).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_18_03 playback_device_create_and_play
  TC_CPP_18_04 playback_duration_position
  TC_CPP_18_05 playback_seek_and_rate
  TC_CPP_18_06 playback_pause_resume_status
  TC_CPP_18_07 playback_status_callback

Requires: test/resource/rosbag/*.bag file.
"""

import glob
import os
import time

import pytest

from pyorbbecsdk import (
    Config,
    OBFrameAggregateOutputMode,
    OBSensorType,
    PlaybackDevice,
    Pipeline,
)

pytestmark = [pytest.mark.functional]


def _find_playback_bag() -> str:
    """Find a .bag file in the test/resource/rosbag directory."""
    test_root = os.path.join(os.path.dirname(__file__), "..")
    bag_dir = os.path.join(test_root, "resource", "rosbag")
    bags = glob.glob(os.path.join(bag_dir, "*.bag"))
    if bags:
        return bags[0]
    return ""


def _get_playbag_or_skip() -> str:
    bag = _find_playback_bag()
    if not bag:
        pytest.skip("No playback .bag file found in test/resource/rosbag/")
    return bag


def _collect_depth_frames_from_playback(pipeline: Pipeline, count=3):
    """Collect depth frames from a playback pipeline."""
    frames_list = []
    deadline = time.time() + count * 5
    while len(frames_list) < count and time.time() < deadline:
        fs = pipeline.wait_for_frames(3000)
        if fs:
            depth = fs.get_depth_frame()
            if depth:
                frames_list.append(depth)
    return frames_list


class TC_CPP_18_Playback:
    """Tests for playback device functionality (no hardware required)."""

    def test_playback_device_create_and_play(self):
        """TC_CPP_18_03: PlaybackDevice can be created and used with pipeline."""
        bag_path = _get_playbag_or_skip()
        pb_device = PlaybackDevice(bag_path)
        assert pb_device is not None

        dev_info = pb_device.get_device_info()
        assert dev_info is not None
        assert dev_info.get_name() is not None

        pipeline = Pipeline(pb_device)
        config = Config()
        sensor_list = pb_device.get_sensor_list()
        assert sensor_list is not None
        assert sensor_list.get_count() > 0

        # Enable all available streams
        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            sensor_type = sensor.get_type()
            try:
                profile_list = pipeline.get_stream_profile_list(sensor_type)
                profile = profile_list.get_default_video_stream_profile()
                config.enable_stream(profile)
            except Exception:
                pass

        config.set_frame_aggregate_output_mode(
            OBFrameAggregateOutputMode.FULL_FRAME_REQUIRE
        )
        pipeline.start(config)

        frames = pipeline.wait_for_frames(5000)
        assert frames is not None, "No frames from playback"

        pipeline.stop()

    def test_playback_duration_position(self):
        """TC_CPP_18_04: Playback duration and position can be queried."""
        bag_path = _get_playbag_or_skip()
        pb_device = PlaybackDevice(bag_path)
        assert pb_device is not None

        duration = pb_device.get_duration()
        assert duration > 0, "Duration should be > 0"

        position = pb_device.get_position()
        assert position >= 0

    def test_playback_seek_and_rate(self):
        """TC_CPP_18_05: Playback seek and rate can be set."""
        bag_path = _get_playbag_or_skip()
        pb_device = PlaybackDevice(bag_path)
        assert pb_device is not None

        duration = pb_device.get_duration()
        if duration > 100:
            pb_device.seek(duration // 2)

        pb_device.set_playback_rate(2.0)
        pb_device.set_playback_rate(0.5)
        pb_device.set_playback_rate(1.0)

    def test_playback_pause_resume_status(self):
        """TC_CPP_18_06: Playback can be paused and resumed."""
        bag_path = _get_playbag_or_skip()
        pb_device = PlaybackDevice(bag_path)
        assert pb_device is not None

        pipeline = Pipeline(pb_device)
        config = Config()
        sensor_list = pb_device.get_sensor_list()
        assert sensor_list is not None
        assert sensor_list.get_count() > 0

        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            sensor_type = sensor.get_type()
            try:
                profile_list = pipeline.get_stream_profile_list(sensor_type)
                profile = profile_list.get_default_video_stream_profile()
                config.enable_stream(profile)
            except Exception:
                pass

        config.set_frame_aggregate_output_mode(
            OBFrameAggregateOutputMode.FULL_FRAME_REQUIRE
        )
        pipeline.start(config)

        # Wait for frames to validate runtime behavior
        pipeline.wait_for_frames(2000)

        # Pause
        pb_device.pause()
        status = pb_device.get_playback_status()
        from pyorbbecsdk import OBPlaybackStatus
        assert status == OBPlaybackStatus.PAUSED

        # Resume
        pb_device.resume()
        status = pb_device.get_playback_status()
        assert status == OBPlaybackStatus.PLAYING

        pipeline.stop()

    def test_playback_status_callback(self):
        """TC_CPP_18_07: Playback status change callback is triggered."""
        bag_path = _get_playbag_or_skip()
        pb_device = PlaybackDevice(bag_path)
        assert pb_device is not None

        cb_count = [0]

        def status_cb(status):
            cb_count[0] += 1

        pb_device.set_playback_status_change_callback(status_cb)

        pipeline = Pipeline(pb_device)
        config = Config()
        sensor_list = pb_device.get_sensor_list()
        assert sensor_list is not None
        assert sensor_list.get_count() > 0

        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            sensor_type = sensor.get_type()
            try:
                profile_list = pipeline.get_stream_profile_list(sensor_type)
                profile = profile_list.get_default_video_stream_profile()
                config.enable_stream(profile)
            except Exception:
                pass

        config.set_frame_aggregate_output_mode(
            OBFrameAggregateOutputMode.FULL_FRAME_REQUIRE
        )
        pipeline.start(config)

        time.sleep(0.5)

        pb_device.pause()
        time.sleep(0.2)

        pb_device.resume()
        time.sleep(0.2)

        pipeline.stop()

        assert cb_count[0] >= 1, "No status change callback received"
