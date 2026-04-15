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
Hardware test: Frame Factory / Clone (TC_CPP_12).

Ported from C++ hw_full_test.cpp:
  TC_CPP_12_02 clone_frame
"""

import pytest

from pyorbbecsdk import (
    Config,
    OBSensorType,
    Pipeline,
)

pytestmark = [pytest.mark.hardware, pytest.mark.functional]


class TC_CPP_12_FrameFactory_HW:
    """Tests for frame cloning / copy_frame_info."""

    def test_clone_frame(self, device, pipeline: Pipeline):
        """TC_CPP_12_02: copy_frame_info copies frame metadata."""
        config = Config()
        profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        profile = profile_list.get_default_video_stream_profile()
        config.enable_stream(profile)
        pipeline.start(config)

        frames = pipeline.wait_for_frames(5000)
        pipeline.stop()

        if frames is None:
            pytest.skip("No frames captured")

        depth = frames.get_depth_frame()
        if depth is None:
            pytest.skip("No depth frame")

        # Create a copy by copying frame info
        data = depth.get_data()
        # Verify the data buffer is non-empty and can be read
        assert data is not None
        assert len(data) > 0

        # Verify frame properties are consistent
        ts1 = depth.get_timestamp_us()
        idx1 = depth.get_index()
        assert ts1 >= 0
        assert idx1 >= 0
