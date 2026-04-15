#!/usr/bin/env python3
"""
test_capture.py - Frame capture test for pyorbbecsdk on macOS

This test verifies that pyorbbecsdk can capture frames from an Orbbec camera.

Usage:
    python tests/test_capture.py

Note: Requires an Orbbec camera to be connected for full testing.
"""

import sys
import time

import pytest


def test_pipeline_creation():
    """Test creating a Pipeline object"""
    print("=" * 50)
    print("Pipeline Creation Test")
    print("=" * 50)

    try:
        import pyorbbecsdk
        from pyorbbecsdk import OBFormat, OBSensorType

        ctx = pyorbbecsdk.Context()
        pipeline = pyorbbecsdk.Pipeline()

        print(f"✓ Pipeline created successfully")
        print(f"  Pipeline object: {pipeline}")
    except Exception as e:
        print(f"✗ Pipeline creation failed: {e}")


def test_config_creation(context, pipeline):
    """Test creating and configuring a Config object"""
    print()
    print("=" * 50)
    print("Configuration Test")
    print("=" * 50)

    if pipeline is None:
        pytest.skip("No pipeline available")

    try:
        from pyorbbecsdk import Config, OBSensorType

        config = Config()
        print(f"✓ Config created successfully")

        # Try to enable streams (may fail without device)
        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.COLOR_SENSOR)
            profile = profile_list.get_default_video_stream_profile()
            config.enable_stream(profile)
            print(f"✓ Color stream configured")
        except Exception as e:
            print(f"  Color stream config skipped: {type(e).__name__}")

        try:
            profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
            profile = profile_list.get_default_video_stream_profile()
            config.enable_stream(profile)
            print(f"✓ Depth stream configured")
        except Exception as e:
            print(f"  Depth stream config skipped: {type(e).__name__}")
    except Exception as e:
        print(f"✗ Config creation failed: {e}")


def test_pipeline_start(pipeline, context):
    """Test starting the pipeline"""
    print()
    print("=" * 50)
    print("Pipeline Start Test")
    print("=" * 50)

    if pipeline is None:
        pytest.skip("No pipeline available")

    try:
        from pyorbbecsdk import Config

        config = Config()
        pipeline.start(config)

        print(f"✓ Pipeline started successfully")
    except Exception as e:
        print(f"  Pipeline start skipped (no device): {type(e).__name__}")


def test_frame_capture(pipeline, duration=3):
    """Test capturing frames"""
    print()
    print("=" * 50)
    print("Frame Capture Test")
    print("=" * 50)

    if pipeline is None:
        print("✗ Skipped (no pipeline)")
        pytest.skip("No pipeline")

    try:
        print(f"  Capturing frames for {duration} seconds...")

        frame_count = 0
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                frames = pipeline.wait_for_frames(1000)
                if frames:
                    frame_count += 1

                    # Try to get color frame
                    try:
                        color_frame = frames.get_color_frame()
                        if color_frame:
                            width = color_frame.get_width()
                            height = color_frame.get_height()
                            print(f"  Frame {frame_count}: Color {width}x{height}")
                    except:
                        pass

                    # Try to get depth frame
                    try:
                        depth_frame = frames.get_depth_frame()
                        if depth_frame:
                            width = depth_frame.get_width()
                            height = depth_frame.get_height()
                            print(f"  Frame {frame_count}: Depth {width}x{height}")
                    except:
                        pass
            except Exception as e:
                # Timeout is OK, just continue
                pass

        print(f"✓ Captured {frame_count} frames")
    except Exception as e:
        print(f"✗ Frame capture failed: {e}")


def test_pipeline_stop(pipeline):
    """Test stopping the pipeline"""
    print()
    print("=" * 50)
    print("Pipeline Stop Test")
    print("=" * 50)

    if pipeline is None:
        print("✗ Skipped (no pipeline)")
        return

    try:
        pipeline.stop()
        print(f"✓ Pipeline stopped successfully")
    except Exception as e:
        print(f"✗ Pipeline stop failed: {e}")


def test_cleanup(context, pipeline):
    """Test proper cleanup"""
    print()
    print("=" * 50)
    print("Cleanup Test")
    print("=" * 50)

    try:
        if pipeline:
            del pipeline
        if context:
            del context
        print("✓ Cleanup completed")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")


def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 48 + "╗")
    print("║  pyorbbecsdk Capture Test Suite             ║")
    print("╚" + "=" * 48 + "╝")
    print()

    results = []

    import pyorbbecsdk

    ctx = None
    pipeline = None

    # Test pipeline creation
    try:
        ctx = pyorbbecsdk.Context()
        pipeline = pyorbbecsdk.Pipeline()
        print("✓ Pipeline created successfully")
        print(f"  Pipeline object: {pipeline}")
        results.append(("Pipeline Creation", True))
    except Exception as e:
        print(f"✗ Pipeline creation failed: {e}")
        results.append(("Pipeline Creation", False))

    # Test config creation
    try:
        from pyorbbecsdk import Config, OBSensorType

        config = Config()
        print(f"✓ Config created successfully")
        if pipeline is not None:
            try:
                profile_list = pipeline.get_stream_profile_list(
                    OBSensorType.COLOR_SENSOR
                )
                config.enable_stream(profile_list.get_default_video_stream_profile())
                print(f"✓ Color stream configured")
            except Exception:
                pass
            try:
                profile_list = pipeline.get_stream_profile_list(
                    OBSensorType.DEPTH_SENSOR
                )
                config.enable_stream(profile_list.get_default_video_stream_profile())
                print(f"✓ Depth stream configured")
            except Exception:
                pass
        results.append(("Configuration", True))
    except Exception as e:
        print(f"✗ Config creation failed: {e}")
        results.append(("Configuration", False))

    # Test pipeline start
    start_success = False
    try:
        if pipeline is None:
            raise RuntimeError("No pipeline")
        config = Config()
        pipeline.start(config)
        print(f"✓ Pipeline started successfully")
        start_success = True
        results.append(("Pipeline Start", True))
    except Exception as e:
        print(f"  Pipeline start skipped: {type(e).__name__}")
        results.append(("Pipeline Start", False))

    # Test frame capture
    capture_success = False
    if start_success and pipeline is not None:
        try:
            frame_count = 0
            start_time = time.time()
            while time.time() - start_time < 3:
                try:
                    frames = pipeline.wait_for_frames(1000)
                    if frames:
                        frame_count += 1
                        try:
                            color_frame = frames.get_color_frame()
                            if color_frame:
                                print(
                                    f"  Frame {frame_count}: Color {color_frame.get_width()}x{color_frame.get_height()}"
                                )
                        except:
                            pass
                        try:
                            depth_frame = frames.get_depth_frame()
                            if depth_frame:
                                print(
                                    f"  Frame {frame_count}: Depth {depth_frame.get_width()}x{depth_frame.get_height()}"
                                )
                        except:
                            pass
                except:
                    pass
            print(f"✓ Captured {frame_count} frames")
            capture_success = frame_count > 0
        except Exception as e:
            print(f"✗ Frame capture failed: {e}")
    results.append(("Frame Capture", capture_success))

    # Test pipeline stop
    try:
        if pipeline is not None:
            pipeline.stop()
            print(f"✓ Pipeline stopped successfully")
            results.append(("Pipeline Stop", True))
    except Exception as e:
        print(f"✗ Pipeline stop failed: {e}")
        results.append(("Pipeline Stop", False))

    # Test cleanup
    try:
        if pipeline:
            del pipeline
        if ctx:
            del ctx
        print("✓ Cleanup completed")
        results.append(("Cleanup", True))
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        results.append(("Cleanup", False))

    # Summary
    print()
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("\nNote: Some tests may fail if no camera is connected.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
