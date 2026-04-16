#!/usr/bin/env python3
"""
test_import.py - Basic import test for pyorbbecsdk on macOS

This test verifies that the pyorbbecsdk module can be imported successfully
and that all required libraries are loaded correctly.

Usage:
    python tests/test_import.py
"""

import platform
import sys


def _check_import():
    """Import pyorbbecsdk. Returns (module_or_None, success)."""
    try:
        import pyorbbecsdk

        print(f"  Module location: {pyorbbecsdk.__file__}")
        if hasattr(pyorbbecsdk, "__version__"):
            print(f"  Version: {pyorbbecsdk.__version__}")
        return pyorbbecsdk, True
    except ImportError as e:
        print(f"  Import failed: {e}")
        return None, False
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return None, False


def _check_attributes(mod):
    """Check expected module attributes exist. Returns True if all present."""
    expected_attrs = [
        "Context",
        "Device",
        "Pipeline",
        "Config",
        "FrameSet",
        "Frame",
        "StreamProfile",
        "StreamProfileList",
    ]
    missing = []
    for attr in expected_attrs:
        if hasattr(mod, attr):
            print(f"  {attr}")
        else:
            print(f"  {attr} (missing)")
            missing.append(attr)
    if missing:
        print(f"  Missing attributes: {', '.join(missing)}")
        return False
    return True


def _check_library_loading(mod):
    """Check native library loading. Returns True on success."""
    try:
        module_file = mod.__file__
        print(f"  Module file: {module_file}")
        if module_file.endswith(".so") or module_file.endswith(".dylib") or module_file.endswith(".pyd"):
            print(f"  Native extension detected")
        else:
            print(f"  Note: Module is not a direct shared library")
        return True
    except Exception as e:
        print(f"  Library loading test failed: {e}")
        return False


def test_platform():
    """Print platform information"""
    print("=" * 50)
    print("Platform Information")
    print("=" * 50)
    print(f"  System: {platform.system()}")
    print(f"  Release: {platform.release()}")
    print(f"  Version: {platform.version()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  Python Implementation: {platform.python_implementation()}")


def test_import():
    """Test basic import of pyorbbecsdk"""
    print("=" * 50)
    print("Import Test")
    print("=" * 50)
    _, ok = _check_import()
    assert ok, "pyorbbecsdk import failed"


def test_module_attributes():
    """Test that expected module attributes exist"""
    print("=" * 50)
    print("Module Attributes Test")
    print("=" * 50)
    mod, ok = _check_import()
    if not ok:
        print("  Skipped (module not imported)")
        return
    result = _check_attributes(mod)
    assert result, "Missing module attributes"


def test_library_loading():
    """Test that native libraries are loaded correctly"""
    print("=" * 50)
    print("Library Loading Test")
    print("=" * 50)
    mod, ok = _check_import()
    if not ok:
        print("  Skipped (module not imported)")
        return
    result = _check_library_loading(mod)
    assert result, "Library loading check failed"


def main():
    """Run all tests"""
    print()
    print("Import Test Suite")
    print("=" * 50)

    results = []

    test_platform()
    results.append(("Platform", True))

    mod, ok = _check_import()
    results.append(("Import", ok))

    if ok:
        result = _check_attributes(mod)
        results.append(("Attributes", result))
        result = _check_library_loading(mod)
        results.append(("Library Loading", result))
    else:
        results.append(("Attributes", False))
        results.append(("Library Loading", False))

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
