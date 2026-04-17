# pyorbbecsdk Test Suite

This directory contains the pytest-based test suite for pyorbbecsdk.
Tests cover device discovery, sensor controls, stream validation, post-processing filters, calibration, and performance benchmarks — organized by device family and test category.

---

## Prerequisites

1. **Install pyorbbecsdk** (or build from source — see [CONTRIBUTING.md](../.github/CONTRIBUTING.md#building-from-source))
2. **Install test dependencies:**
   ```bash
   pip install -r test/requirements_test.txt
   ```
3. **One-time OS setup (hardware tests only):**
   - **Linux:** install udev rules so the SDK can open USB devices
     ```bash
     cd scripts/env_setup && sudo ./install_udev_rules.sh
     sudo udevadm control --reload && sudo udevadm trigger
     ```
   - **Windows:** register frame metadata (required for timestamps)
     ```powershell
     # Run PowerShell as Administrator
     cd scripts\env_setup
     .\obsensor_metadata_win10.ps1 -op install_all
     ```

---

## Running Tests Manually

All commands are run from the **repository root**.

### Quick check — no camera needed

```bash
pytest test/nohw/ -v
# or equivalently:
pytest test/ -m "not hardware" -v
```

### Run hardware tests

```bash
pytest test/hw/ -m hardware -v          # Generic hardware tests
pytest test/device/ -m hardware -v      # Device-specific tests
pytest test/thread_safety/ -v           # Thread safety tests
pytest test/perf/ -v                    # Performance benchmarks
```

### Run by device marker

```bash
pytest test/ -m g300_series -v   # G300 series (Gemini 330/335/336/305/345)
pytest test/ -m femto       -v   # Femto Bolt/Mega
pytest test/ -m astra_mini  -v   # Astra Mini
pytest test/ -m astra2      -v   # Astra 2
pytest test/ -m hardware    -v   # All hardware tests
```

### Run by category

```bash
pytest test/ -m functional   -v   # API correctness only
pytest test/ -m stability    -v   # Reliability/sync only
pytest test/ -m performance  -v   # Benchmarks only
```

### Combine device + category

```bash
pytest test/ -m "g300_series and functional"  -v
pytest test/ -m "femto and stability"         -v
pytest test/ -m "not performance"             -v   # skip benchmarks
```

### Full test session

```bash
pytest test/ -v
```

---

## Test Markers

### Device / scope markers

| Marker | Meaning | Auto-skip condition |
|--------|---------|---------------------|
| `hardware` | Requires a physical Orbbec camera | No device connected |
| `g300_series` | Any Gemini 330/335/336/305/345 variant | Wrong device family |
| `femto` | Femto Bolt or Femto Mega | Wrong device family |
| `astra_mini` | Astra Mini Pro / S Pro | Wrong device family |
| `astra2` | Astra 2 | Wrong device family |

> **Tip:** If the wrong camera is connected, device-specific tests skip automatically with a clear message — they do **not** fail.

### Category markers

| Marker | Meaning | Typical duration |
|--------|---------|-----------------|
| `functional` | API correctness — device info, stream start, sensor controls, calibration, filters | seconds |
| `stability` | Multi-frame reliability — timestamp monotonicity, sync accuracy, drop rate | 10–30 s |
| `performance` | Long-running benchmarks — FPS, latency, throughput | 60+ s |

Category markers compose freely with device markers:

```bash
pytest test/ -m "g300_series and stability" -v
pytest test/ -m "not performance"           -v
```

---

## Test Directory Map

### Category key: `F` = functional · `S` = stability · `P` = performance

### nohw/ (no camera needed)

| File | Category | What it tests |
|------|----------|---------------|
| `test_context.py` | F | Context API: device enumeration, logging, callbacks |
| `test_logger.py` | F | Logger severity, file, console, callback |
| `test_filter.py` | F | Filter parameters, factory |
| `test_frame.py` | F | Frame types, factory |
| `test_data_struct.py` | F | Data structures (Rect, Intrinsics, etc.) |
| `test_coord_transform.py` | F | Coordinate transform utilities |
| `test_error.py` | F | Error handling and exception types |
| `test_version.py` | F | SDK version info |
| `test_playback.py` | F | BAG file playback (deviceless) |

### hw/ (any Orbbec camera)

| File | Category | What it tests |
|------|----------|---------------|
| `test_pipeline.py` | F | Pipeline start/stop, frame capture |
| `test_sensor.py` | F | Sensor enumeration and properties |
| `test_device_access.py` | F | Device access modes, state |
| `test_device_list.py` | F | Device list enumeration |
| `test_firmware.py` | F | Firmware version, upgrade checks |
| `test_property.py` | F | Property get/set across sensor types |
| `test_preset.py` | F | Preset configurations |
| `test_config.py` | F | Stream configuration |
| `test_stream_profile.py` | F | Stream profile validation |
| `test_depth_mode.py` | F | Depth work modes |
| `test_filter.py` | F | Post-processing filters on live frames |
| `test_frame_metadata.py` | F | Frame metadata fields |
| `test_frame_factory.py` | F | Frame factory methods |
| `test_frame_interleave.py` | F | Frame interleaving |
| `test_record_playback.py` | F | Record to BAG, playback |
| `test_error_safety.py` | F | Error safety with hardware |
| `test_data_struct.py` | F | Data structures with device |
| `test_discovery.py` | F | Device discovery |

### device/ (device-specific, marked with device family)

| File | Marker | What it tests |
|------|--------|---------------|
| `test_g300_series_device.py` | g300_series | Device identity, all G300 sensor requirements |
| `test_g300_series_controls.py` | g300_series | Depth/Color/IR/Laser/HDR property read-write |
| `test_g300_series_filters.py` | g300_series | Full post-processing filter pipeline |
| `test_g300_series_calib.py` | g300_series | Intrinsics, distortion, extrinsic orthogonality |
| `test_g300_series_streams.py` | g300_series | Stream validity, FPS, multi-stream sync, timestamps |
| `test_g300_series_performance.py` | g300_series | Startup latency, 60 s FPS stability, restart time |
| `test_femto_device.py` | femto | Identity, ToF sensors (Depth, Color, Left/Right IR, IMU) |
| `test_femto_controls.py` | femto | Depth/Color/Laser property read-write |
| `test_femto_calib.py` | femto | Intrinsics, distortion, extrinsic orthogonality |
| `test_femto_streams.py` | femto | Depth (ToF range 300–8000 mm), Color, IR, IMU, sync |
| `test_astra_mini_device.py` | astra_mini | Device identity, sensors, calibration |
| `test_astra_mini_streams.py` | astra_mini | Depth, Color, IR, controls, timestamps |
| `test_astra2_device.py` | astra2 | Device identity, sensors, depth work mode |
| `test_astra2_streams.py` | astra2 | Depth, Color, IR, sync, controls |

### perf/ (performance benchmarks)

| File | Category | What it tests |
|------|----------|---------------|
| `test_frame_drop.py` | P | Frame drop rate under sustained streaming |

### thread_safety/ (concurrent access)

| File | Category | What it tests |
|------|----------|---------------|
| `test_concurrent_access.py` | F + S | Thread-safe SDK API usage from multiple threads |

### scenario/ (end-to-end scenarios)

| File | What it tests |
|------|---------------|
| `test_log_completeness.py` | Logger completeness in real-world scenarios |

### examples_tests/ (example validation infrastructure)

| File | What it does |
|------|--------------|
| `generate_examples_manifest.py` | Discovers and catalogs all SDK examples |
| `generate_ci_matrix.py` | Generates CI matrix from manifest + runner pools |
| `run_examples_suite.py` | Runs examples and collects results |
| `merge_example_results.py` | Merges multiple example result files |
| `examples_test_utils.py` | Shared utilities for example tests |

---

## Generating HTML Test Reports

```bash
# No-hardware tests
pytest test/nohw/ -v --html=reports/nohw_report.html --self-contained-html

# Hardware tests
pytest test/hw/ test/device/ -m hardware -v --html=reports/hw_report.html --self-contained-html

# Full suite
pytest test/ -v --html=reports/full_report.html --self-contained-html
```

Reports are saved to `reports/`. Open the HTML file in any browser to view.

---

## Device Depth Range Reference

| Device Family | Min Depth | Max Depth | Sensor Type |
|---------------|-----------|-----------|-------------|
| G300 series (330/335/336) | ~20 mm | ~10 000 mm | Structured light |
| G300 series (305/345) | ~20 mm | ~10 000 mm | Structured light |
| Femto Bolt / Mega | 300 mm | 8 000 mm | Time-of-Flight (ToF) |
| Astra Mini Pro | 300 mm | 8 000 mm | Structured light |
| Astra 2 | 300 mm | 10 000 mm | Structured light |

---

## Adding New Device Tests

To add tests for a new device family:

1. **Register the fixture** in `conftest.py`:
   ```python
   @pytest.fixture(scope="session")
   def my_device_fixture(device, device_info):
       name = device_info.get_name() or ""
       if "My Device Name" not in name:
           pytest.skip(f"Not My Device, got '{name}'")
       return device
   ```

2. **Register the marker** in `conftest.py`:
   ```python
   config.addinivalue_line("markers", "my_device: test for My Device")
   ```

3. **Create test files** following the naming pattern:
   ```
   test_my_device_device.py    # device discovery + sensors       → functional
   test_my_device_streams.py   # stream validation + timestamps   → functional + stability
   test_my_device_controls.py  # property get/set                 → functional
   ```

4. **Mark tests** with `hardware`, device marker, and category markers:
   ```python
   # device + functional tests
   pytestmark = [pytest.mark.hardware, pytest.mark.my_device, pytest.mark.functional]

   # stream tests (functional correctness + stability)
   pytestmark = [pytest.mark.hardware, pytest.mark.my_device,
                 pytest.mark.functional, pytest.mark.stability]
   ```

5. **Register the device name prefix** in `conftest.py` under `_DEVICE_NAME_PATTERNS` so the `device` fixture can auto-detect it.
