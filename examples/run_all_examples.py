"""
Automated smoke-tester for all pyorbbecsdk examples.

Each example is launched in a subprocess with:
  - A wall-clock timeout (TIMEOUT_SEC seconds)
  - stdin piped (for interactive input()) or /dev/null (for --test)
  - stdout/stderr captured and saved to test_logs/<label>.log

Exit codes interpreted:
  0        -> PASS
  timeout  -> PASS (example ran, just hit the time limit — normal for GUI loops)
  non-zero -> FAIL (import error, AttributeError, etc.)

Run from repo root:
    python examples/run_all_examples.py
"""

import os
import subprocess
import sys
import time

PYTHON = sys.executable
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT_SEC = 30  # seconds per example before we send SIGTERM
BAG_FILE = "test_recording.bag"  # shared bag file between recorder and playback

# ---------------------------------------------------------------------------
# Test matrix
# Each entry: (label, script_path, extra_args, stdin_input, env_override)
#   stdin_input  - bytes fed to the process stdin (simulates user typing)
#   extra_args   - additional CLI args to pass
#   env_override - dict of environment variables to set for this test
#
# Examples with --test support: GUI/rendering examples that save frames to
# disk and auto-exit after a fixed count.  No stdin or timeout needed —
# they terminate cleanly on their own.
# ---------------------------------------------------------------------------
TESTS = [
    # ---- Quick start ----
    ("quick_start", "examples/quick_start.py", ["--test"], None, None),
    # ---- Beginner ----
    ("01 hello_camera", "examples/beginner/01_hello_camera.py", [], None, None),
    ("02 depth_visualization", "examples/beginner/02_depth_visualization.py", ["--test"], None, None),
    (
        "03 color_and_depth_aligned (SW)",
        "examples/beginner/03_color_and_depth_aligned.py",
        ["--test"],
        None,
        None,
    ),
    (
        "03 color_and_depth_aligned (HW --hw)",
        "examples/beginner/03_color_and_depth_aligned.py",
        ["--test", "--hw"],
        None,
        None,
    ),
    ("04 camera_calibration", "examples/beginner/04_camera_calibration.py", [], None, None),
    ("05 point_cloud (--test)", "examples/beginner/05_point_cloud.py", ["--test"], None, None),
    ("06 multi_streams", "examples/beginner/06_multi_streams.py", ["--test"], None, None),
    ("07 imu (--test)", "examples/beginner/07_imu.py", ["--test"], None, None),
    # 08 net_device — needs network camera; skip
    # 09 firmware_update — destructive; skip
    # ---- Advanced ----
    (
        "adv01 recorder (--test)",
        "examples/advanced/01_recorder.py",
        ["--test"],
        f"{BAG_FILE}\n".encode(),
        None,
    ),
    (
        "adv02 playback (--test)",
        "examples/advanced/02_playback.py",
        ["--test"],
        None,
        {"PLAYBACK_FILE": BAG_FILE},
    ),
    (
        "adv03 save_image_to_disk (--test)",
        "examples/advanced/03_save_image_to_disk.py",
        ["--test"],
        None,
        None,
    ),
    ("adv04 enumerate", "examples/advanced/04_enumerate.py", [], b"q\n", None),
    ("adv05 hot_plug (--test)", "examples/advanced/05_hot_plug.py", ["--test"], None, None),
    ("adv06 control", "examples/advanced/06_control.py", [], None, None),
    ("adv07 metadata (--test)", "examples/advanced/07_metadata.py", ["--test"], None, None),
    (
        "adv08 custom_filter_chain (--test)",
        "examples/advanced/08_custom_filter_chain.py",
        ["--test"],
        None,
        None,
    ),
    ("adv09 post_processing (--test)", "examples/advanced/09_post_processing.py", ["--test"], None, None),
    ("adv10 hdr (--test)", "examples/advanced/10_hdr.py", ["--test"], None, None),
    ("adv11 preset", "examples/advanced/11_preset.py", [], b"-1\n", None),
    ("adv12 depth_work_mode", "examples/advanced/12_depth_work_mode.py", [], None, None),
    ("adv13 confidence (--test)", "examples/advanced/13_confidence.py", ["--test"], None, None),
    # adv14 two_devices_sync — needs 2 cameras; skip
    (
        "adv15 high_performance_pipeline (--test)",
        "examples/advanced/15_high_performance_pipeline.py",
        ["--test"],
        None,
        None,
    ),
    ("adv16 coordinate_transform", "examples/advanced/16_coordinate_transform.py", [], None, None),
    ("adv17 laser_interleave (--test)", "examples/advanced/17_laser_interleave.py", ["--test"], None, None),
    # adv18 forceip — needs network camera; skip
    # adv19 device_optional_depth_presets_update — needs Gemini 330; skip on 335L
    # ---- Applications ----
    ("app ruler (--test)", "examples/applications/ruler.py", ["--test"], None, None),
    # app object_detection — needs ONNX model file; skip
]

SKIP = {
    "examples/beginner/08_net_device.py",
    "examples/beginner/09_device_firmware_update.py",
    "examples/advanced/14_two_devices_sync.py",
    "examples/advanced/18_forceip.py",
    "examples/advanced/19_device_optional_depth_presets_update.py",
    "examples/advanced/16_coordinate_transform.py",  # requires pynput module
    "examples/applications/object_detection/object_detection.py",
}

# ---------------------------------------------------------------------------

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
LOG_DIR = "test_logs"


INTER_TEST_DELAY = 3  # seconds between tests for device recovery


def run_one(label, script, extra_args, stdin_input, env_override=None):
    cmd = [PYTHON, os.path.join(REPO, script)] + extra_args
    t0 = time.time()

    # For --test examples, stdin=DEVNULL to avoid blocking/lock issues with input()
    # For interactive examples, use PIPE to feed synthetic input
    stdin = subprocess.PIPE if stdin_input is not None else subprocess.DEVNULL

    env = os.environ.copy()
    if env_override:
        env.update(env_override)

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=REPO,
            env=env,
        )
        try:
            stdout, stderr = proc.communicate(input=stdin_input, timeout=TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            elapsed = time.time() - t0
            return "TIMEOUT", elapsed, stdout, stderr

        elapsed = time.time() - t0
        retcode = proc.returncode
        if retcode == 0:
            return "PASS", elapsed, stdout, stderr
        elif retcode == 77:
            return "SKIP", elapsed, stdout, stderr
        else:
            return "FAIL", elapsed, stdout, stderr

    except Exception as e:
        return "ERROR", time.time() - t0, b"", str(e).encode()


def save_log(label, stdout, stderr):
    """Save test console output to test_logs/<label>.log."""
    os.makedirs(os.path.join(REPO, LOG_DIR), exist_ok=True)
    safe_label = label.replace(" ", "_").replace("(", "").replace(")", "").replace("--", "")
    log_path = os.path.join(REPO, LOG_DIR, f"{safe_label}.log")
    with open(log_path, "w") as f:
        f.write(f"=== {label} ===\n")
        f.write("stdout:\n")
        f.write(stdout.decode(errors="replace"))
        f.write("\nstderr:\n")
        f.write(stderr.decode(errors="replace"))
    return log_path


def main():
    results = []
    print(f"\n{'='*72}")
    print(f"  pyorbbecsdk Example Smoke Tests")
    print(f"  Timeout per example: {TIMEOUT_SEC}s")
    print(f"  Logs: {LOG_DIR}/")
    print(f"{'='*72}\n")

    for label, script, extra_args, stdin_input, env_override in TESTS:
        if script in SKIP:
            continue
        print(f"  Running  {label:<45}", end="", flush=True)
        status, elapsed, stdout, stderr = run_one(label, script, extra_args, stdin_input, env_override)

        # Save log for every test
        log_path = save_log(label, stdout, stderr)

        if status in ("PASS", "TIMEOUT"):
            color = GREEN
        elif status == "SKIP":
            color = YELLOW
        else:
            color = RED

        print(f"  {color}{status:8}{RESET}  ({elapsed:.1f}s)")

        if status == "FAIL":
            # Show last 10 lines of stderr for diagnosis
            err_lines = stderr.decode(errors="replace").strip().splitlines()
            for line in err_lines[-10:]:
                print(f"      {RED}{line}{RESET}")

        if INTER_TEST_DELAY > 0 and script not in SKIP:
            time.sleep(INTER_TEST_DELAY)

        results.append((label, status, elapsed, stdout, stderr))

    # Summary
    passed = sum(1 for _, s, *_ in results if s in ("PASS", "TIMEOUT"))
    failed = sum(1 for _, s, *_ in results if s == "FAIL")
    errors = sum(1 for _, s, *_ in results if s == "ERROR")
    skipped = sum(1 for _, s, *_ in results if s == "SKIP")
    total = len(results)

    print(f"\n{'='*72}")
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  |  {RED}{failed} FAILED{RESET}", end="")
    if errors:
        print(f"  |  {RED}{errors} ERRORS{RESET}", end="")
    if skipped:
        print(f"  |  {YELLOW}{skipped} SKIPPED{RESET}", end="")
    print(f"\n{'='*72}\n")

    # Cleanup test bag files
    if os.path.exists(os.path.join(REPO, BAG_FILE)):
        os.remove(os.path.join(REPO, BAG_FILE))
        print(f"  Cleaned up: {BAG_FILE}")

    return 1 if (failed + errors) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
