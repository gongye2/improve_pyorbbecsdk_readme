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
No-hardware test: Coordinate Transform (TC_CPP_20).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_20_01 3d_to_3d
  TC_CPP_20_02 2d_depth_to_3d
  TC_CPP_20_03 3d_to_2d
  TC_CPP_20_04 2d_to_2d
"""

import numpy as np
import pytest

from pyorbbecsdk import (
    OBCameraDistortion,
    OBCameraIntrinsic,
    OBExtrinsic,
    OBPoint2f,
    OBPoint3f,
    transformation2dto2d,
    transformation2dto3d,
    transformation3dto2d,
    transformation3dto3d,
)

pytestmark = [pytest.mark.functional]


def _make_identity_extrinsic() -> OBExtrinsic:
    """Create an identity extrinsic (no rotation, no translation)."""
    ex = OBExtrinsic()
    ex.rot = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
    ex.transform = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    return ex


def _make_test_intrinsic() -> OBCameraIntrinsic:
    """Create a test camera intrinsic."""
    intr = OBCameraIntrinsic()
    intr.fx = 500.0
    intr.fy = 500.0
    intr.cx = 320.0
    intr.cy = 240.0
    intr.width = 640
    intr.height = 480
    return intr


def _make_zero_distortion() -> OBCameraDistortion:
    """Create zero distortion parameters."""
    d = OBCameraDistortion()
    d.k1 = 0.0
    d.k2 = 0.0
    d.k3 = 0.0
    d.k4 = 0.0
    d.k5 = 0.0
    d.k6 = 0.0
    d.p1 = 0.0
    d.p2 = 0.0
    return d


class TC_CPP_20_CoordTransform:
    """Tests for coordinate transformation functions."""

    def test_3d_to_3d(self):
        """TC_CPP_20_01: 3D-to-3D transform with identity and known translation."""
        src = OBPoint3f()
        src.x = 100.0
        src.y = 200.0
        src.z = 300.0

        # Identity extrinsic: output should equal input
        identity = _make_identity_extrinsic()
        dst = transformation3dto3d(src, identity)
        assert abs(dst.x - src.x) < 1e-3
        assert abs(dst.y - src.y) < 1e-3
        assert abs(dst.z - src.z) < 1e-3

        # Known translation: output = input + translation
        with_trans = _make_identity_extrinsic()
        with_trans.transform = np.array([10.0, 20.0, 30.0], dtype=np.float32)
        dst2 = transformation3dto3d(src, with_trans)
        assert abs(dst2.x - (src.x + 10.0)) < 1e-3
        assert abs(dst2.y - (src.y + 20.0)) < 1e-3
        assert abs(dst2.z - (src.z + 30.0)) < 1e-3

    def test_2d_depth_to_3d(self):
        """TC_CPP_20_02: 2D pixel + depth → 3D point."""
        intrinsic = _make_test_intrinsic()
        identity = _make_identity_extrinsic()

        # Image center (cx, cy) + identity extrinsic → 3D point at (0, 0, depth)
        pixel = OBPoint2f()
        pixel.x = 320.0
        pixel.y = 240.0
        point3d = transformation2dto3d(pixel, 1000.0, intrinsic, identity)
        assert abs(point3d.x) < 1.0
        assert abs(point3d.y) < 1.0
        assert abs(point3d.z - 1000.0) < 1.0

    def test_3d_to_2d(self):
        """TC_CPP_20_03: 3D point → 2D pixel projection."""
        intrinsic = _make_test_intrinsic()
        distortion = _make_zero_distortion()
        identity = _make_identity_extrinsic()

        # Point at (0, 0, 1000) with no distortion → projects to principal point (cx, cy)
        src = OBPoint3f()
        src.x = 0.0
        src.y = 0.0
        src.z = 1000.0
        pixel = transformation3dto2d(src, intrinsic, distortion, identity)
        assert abs(pixel.x - 320.0) < 1.0
        assert abs(pixel.y - 240.0) < 1.0

    def test_2d_to_2d(self):
        """TC_CPP_20_04: 2D-to-2D transform between same intrinsics."""
        src_intrinsic = _make_test_intrinsic()
        src_dist = _make_zero_distortion()
        tgt_intrinsic = _make_test_intrinsic()  # Same intrinsics
        tgt_dist = _make_zero_distortion()
        identity = _make_identity_extrinsic()

        # Same intrinsics + identity extrinsic → same pixel
        src_px = OBPoint2f()
        src_px.x = 400.0
        src_px.y = 300.0
        dst_px = transformation2dto2d(
            src_px, 1000.0, src_intrinsic, src_dist, tgt_intrinsic, tgt_dist, identity
        )
        assert abs(dst_px.x - src_px.x) < 2.0
        assert abs(dst_px.y - src_px.y) < 2.0
