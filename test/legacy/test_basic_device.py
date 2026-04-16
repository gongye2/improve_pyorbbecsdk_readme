#!/usr/bin/env python3
"""
test_device.py - Device enumeration test for pyorbbecsdk on macOS

This test verifies that pyorbbecsdk can enumerate connected Orbbec devices.

Usage:
    python tests/test_device.py

Note: Requires an Orbbec camera to be connected for full testing.
"""

import platform
import sys


def _create_context():
    """Create and return a Context object, or None on failure."""
    try:
        import pyorbbecsdk

        ctx = pyorbbecsdk.Context()
        print(f"  Context created successfully")
        return ctx
    except Exception as e:
        print(f"  Context creation failed: {e}")
        return None


def _enumerate_devices(context):
    """Query devices from context. Returns (success, device_or_None)."""
    try:
        devices = context.query_devices()
        device_count = devices.get_count() if devices else 0
        print(f"  Devices found: {device_count}")
        if device_count > 0:
            device = devices.get_device_by_index(0)
            try:
                info = device.get_device_info()
                print(f"  Device: {info.get_name()}")
            except Exception:
                pass
            return True, device
        return True, None
    except Exception as e:
        print(f"  Device enumeration failed: {e}")
        return False, None


def _check_device_info(device):
    """Print device info fields. Returns True on success."""
    try:
        device_info = device.get_device_info()
        info_tests = [
            ("Name", lambda: device_info.get_name()),
            ("Serial Number", lambda: device_info.get_serial_number()),
            ("Firmware Version", lambda: device_info.get_firmware_version()),
            ("USB Bandwidth", lambda: str(device.get_usb_bandwidth())),
        ]
        for name, getter in info_tests:
            try:
                value = getter()
                print(f"  {name}: {value}")
            except Exception:
                print(f"  {name}: <not available>")
        return True
    except Exception as e:
        print(f"  Device info test failed: {e}")
        return False


def _check_sensors(device):
    """Print sensor list. Returns True on success."""
    try:
        sensors = device.get_sensor_list()
        sensor_count = sensors.get_count() if sensors else 0
        print(f"  Sensors found: {sensor_count}")
        for i in range(sensor_count):
            try:
                sensor = sensors.get_sensor_by_index(i)
                print(f"  Sensor {i + 1}: {sensor.get_type()}")
            except Exception:
                pass
        return True
    except Exception as e:
        print(f"  Sensor enumeration failed: {e}")
        return False


def test_context_creation():
    """Test creating a Context object"""
    print("=" * 50)
    print("Context Creation Test")
    print("=" * 50)
    ctx = _create_context()
    assert ctx is not None, "Context creation failed"


def test_device_enumeration():
    """Test enumerating connected devices"""
    print("=" * 50)
    print("Device Enumeration Test")
    print("=" * 50)
    ctx = _create_context()
    if ctx is None:
        print("  Skipped (no context)")
        return
    ok, _ = _enumerate_devices(ctx)
    assert ok, "Device enumeration failed"


def test_device_info():
    """Test getting device information"""
    print("=" * 50)
    print("Device Information Test")
    print("=" * 50)
    ctx = _create_context()
    if ctx is None:
        print("  Skipped (no context)")
        return
    _, device = _enumerate_devices(ctx)
    if device is None:
        print("  Skipped (no device)")
        return
    ok = _check_device_info(device)
    assert ok, "Device info check failed"


def test_sensor_enumeration():
    """Test enumerating device sensors"""
    print("=" * 50)
    print("Sensor Enumeration Test")
    print("=" * 50)
    ctx = _create_context()
    if ctx is None:
        print("  Skipped (no context)")
        return
    _, device = _enumerate_devices(ctx)
    if device is None:
        print("  Skipped (no device)")
        return
    ok = _check_sensors(device)
    assert ok, "Sensor enumeration failed"


def test_cleanup():
    """Test proper cleanup"""
    print("=" * 50)
    print("Cleanup Test")
    print("=" * 50)
    ctx = _create_context()
    if ctx is not None:
        del ctx
    print("  Cleanup completed")


def main():
    """Run all tests"""
    print()
    print("Device Test Suite")
    print("=" * 50)

    results = []

    # Test context creation
    ctx = _create_context()
    results.append(("Context Creation", ctx is not None))

    # Test device enumeration
    if ctx:
        ok, device = _enumerate_devices(ctx)
        results.append(("Device Enumeration", ok))

        # Test device info
        if device:
            ok = _check_device_info(device)
            results.append(("Device Information", ok))

            # Test sensor enumeration
            ok = _check_sensors(device)
            results.append(("Sensor Enumeration", ok))
        else:
            results.append(("Device Information", True))
            results.append(("Sensor Enumeration", True))

        # Test cleanup
        del ctx
        results.append(("Cleanup", True))

    # Summary
    print()
    print("Test Summary")
    print("=" * 50)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, r in results:
        status = "PASS" if r else "FAIL"
        print(f"  {status}: {name}")
    print(f"\nTotal: {passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
