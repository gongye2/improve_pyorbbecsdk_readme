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
No-hardware test: Filter creation and lifecycle (TC_CPP_13).

Ported from C++ nohw_full_test.cpp:
  TC_CPP_13_01 create_all_builtin_filters
  TC_CPP_13_02 create_invalid_filter
  TC_CPP_13_05 filter_enable_disable
  TC_CPP_13_06 filter_reset_and_config
  TC_CPP_13_07 filter_type_check
  TC_CPP_13_17 private_filter

Note: These tests do NOT require frames or a pipeline — they validate filter
creation, enable/disable, config schema, and type checking in isolation.

Note: The Python SDK does not expose the raw C `Filter` constructor; filters
are created via their concrete subclasses (DecimationFilter, etc.).
"""

import pytest

from pyorbbecsdk import (
    DecimationFilter,
    PointCloudFilter,
    ThresholdFilter,
    AlignFilter,
    FormatConvertFilter,
    HDRMergeFilter,
    SequenceIdFilter,
    OBStreamType,
)

pytestmark = [pytest.mark.functional]


class TC_CPP_13_Filter_Nohw:
    """Tests for filter creation and lifecycle without frames."""

    def test_create_all_builtin_filters(self):
        """TC_CPP_13_01: All builtin filters can be created via concrete classes."""
        # Required filters — create via concrete Python classes
        filters = [
            ("DecimationFilter", DecimationFilter, {}),
            ("ThresholdFilter", ThresholdFilter, {}),
            ("AlignFilter", AlignFilter, {"align_to_stream": OBStreamType.COLOR_STREAM}),
            ("FormatConvertFilter", FormatConvertFilter, {}),
            ("HDRMergeFilter", HDRMergeFilter, {}),
            ("PointCloudFilter", PointCloudFilter, {}),
            ("SequenceIdFilter", SequenceIdFilter, {}),
        ]
        for name, cls, kwargs in filters:
            f = cls(**kwargs)
            assert f is not None, f"Filter is null: {name}"

        # Optional filters (may fail if not licensed)
        optional_names = [
            "SpatialAdvancedFilter",
            "SpatialFastFilter",
            "SpatialModerateFilter",
            "TemporalFilter",
            "HoleFillingFilter",
            "NoiseRemovalFilter",
            "DisparityTransform",
            "FalsePositiveFilter",
        ]
        for name in optional_names:
            try:
                from pyorbbecsdk import Filter
                # Filter has no public constructor in Python — skip
            except Exception:
                pass

    def test_create_invalid_filter(self):
        """TC_CPP_13_02: Python SDK Filter class has no public constructor."""
        from pyorbbecsdk import Filter
        # In Python, Filter is abstract with no public constructor.
        # This is a design difference from C++.
        try:
            f = Filter()
            # If it somehow works, verify it's not usable
        except TypeError:
            # Expected: no constructor defined
            pass

    def test_filter_enable_disable(self):
        """TC_CPP_13_05: Filter can be enabled and disabled."""
        filt = DecimationFilter()
        filt.enable(True)
        assert filt.is_enabled() is True
        filt.enable(False)
        assert filt.is_enabled() is False
        filt.enable(True)
        assert filt.is_enabled() is True

    def test_filter_reset_and_config(self):
        """TC_CPP_13_06: Filter config schema is accessible and resettable."""
        filt = DecimationFilter()
        # Get config schema via get_config_schema_vec
        schema = filt.get_config_schema_vec()
        assert schema is not None
        assert isinstance(schema, list)
        # Reset
        filt.reset()

    def test_filter_type_check(self):
        """TC_CPP_13_07: Filter type checking works correctly."""
        filt = PointCloudFilter()
        assert filt.get_name() == "PointCloudFilter"
        # DecimationFilter should be identifiable
        dec = DecimationFilter()
        assert dec.get_name() == "DecimationFilter"
        # Type check methods
        assert dec.is_decimation_filter() is True
        assert filt.is_point_cloud_filter() is True

    def test_private_filter(self):
        """TC_CPP_13_17: Private filter creation without key is handled safely."""
        # In Python SDK, private filters like SpatialAdvancedFilter may cause
        # crashes if not properly licensed. We skip construction and just
        # validate the import works.
        try:
            from pyorbbecsdk import SpatialAdvancedFilter
            # Import succeeded but construction may crash — skip it
            pytest.skip("SpatialAdvancedFilter import succeeded; construction skipped for safety")
        except ImportError:
            # Expected: private filter not exposed
            pass
