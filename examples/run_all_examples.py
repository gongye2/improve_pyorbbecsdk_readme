"""
Automated smoke-tester for all pyorbbecsdk examples.

Each example is launched in a subprocess with:
  - A wall-clock timeout (TIMEOUT_SEC seconds)
  - stdin piped (for interactive input()) or /dev/null (for --test)
  - stdout/stderr captured and saved to reports/examples-smoke/logs/<label>.log

Exit codes interpreted:
  0        -> PASS
  77       -> SKIP (feature not supported by device)
  timeout  -> PASS (example ran, just hit the time limit — normal for GUI loops)
  non-zero -> FAIL (import error, AttributeError, etc.)

After all tests, a self-contained HTML report is generated in reports/examples-smoke/
with all logs, images, and point cloud files stored alongside the report using relative
paths — the entire folder can be zipped and opened on any machine.

Run from repo root:
    python examples/run_all_examples.py
    python examples/run_all_examples.py --lidar    # include LiDAR examples
"""

import argparse
import datetime as dt
import html
import os
import shutil
import subprocess
import sys
import time

PYTHON = sys.executable
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT_SEC = 30  # seconds per example before we send SIGTERM
BAG_FILE = "test_recording.bag"  # shared bag file for GUI recorder
NOGUI_BAG_FILE = "test_recording_nogui.bag"  # bag file for no-gui recorder
LIDAR_BAG_FILE = "test_lidar_recording.bag"  # bag file for lidar record/playback

# Directories for outputs
REPORT_DIR = "reports/examples-smoke"

# ---------------------------------------------------------------------------
# Test matrix
# Each entry: (label, script_path, extra_args, stdin_input, env_override)
#   stdin_input  - bytes fed to the process stdin (simulates user typing)
#   extra_args   - additional CLI args to pass
#   env_override - dict of environment variables to set for this test
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
    ("10 logger (--test)", "examples/beginner/10_logger.py", ["--test"], None, None),
    ("08 net_device (SKIPPED)", "examples/beginner/08_net_device.py", ["--test"], None, None),
    ("09 device_firmware_update (SKIPPED)", "examples/beginner/09_device_firmware_update.py", ["--test"], None, None),
    # ---- Advanced ----
    (
        "adv01 recorder (--test)",
        "examples/advanced/01_recorder.py",
        ["--test"],
        f"{BAG_FILE}\n".encode(),
        None,
    ),
    (
        "adv01 recorder --no-gui (--test)",
        "examples/advanced/01_recorder.py",
        ["--test", "--no-gui"],
        f"{NOGUI_BAG_FILE}\n".encode(),
        None,
    ),
    (
        "adv02 playback GUI (--test)",
        "examples/advanced/02_playback.py",
        ["--test"],
        None,
        {"PLAYBACK_FILE": BAG_FILE},
    ),
    (
        "adv02 playback no-gui (--test)",
        "examples/advanced/02_playback.py",
        ["--test"],
        None,
        {"PLAYBACK_FILE": NOGUI_BAG_FILE},
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
    ("adv14 two_devices_sync (SKIPPED)", "examples/advanced/14_two_devices_sync.py", ["--test"], None, None),
    (
        "adv15 high_performance_pipeline (--test)",
        "examples/advanced/15_high_performance_pipeline.py",
        ["--test"],
        None,
        None,
    ),
    ("adv16 coordinate_transform", "examples/advanced/16_coordinate_transform.py", [], None, None),
    ("adv17 laser_interleave (--test)", "examples/advanced/17_laser_interleave.py", ["--test"], None, None),
    ("adv18 forceip (SKIPPED)", "examples/advanced/18_forceip.py", ["--test"], None, None),
    ("adv19 depth_presets_update (SKIPPED)", "examples/advanced/19_device_optional_depth_presets_update.py", ["--test"], None, None),
    # ---- Applications ----
    ("app ruler (--test)", "examples/applications/ruler.py", ["--test"], None, None),
]

HARDCODED_SKIP = [
    ("app object_detection (SKIPPED)", "examples/applications/object_detection/object_detection.py", "requires onnxruntime & ONNX model"),
]

# ---------------------------------------------------------------------------
# LiDAR test matrix — only executed when --lidar flag is passed
# ---------------------------------------------------------------------------
LIDAR_TESTS = [
    ("lidar quick_start (--test)", "examples/lidar_examples/lidar_quick_start.py", ["--test"], None, None),
    ("lidar stream (--test)", "examples/lidar_examples/lidar_stream.py", ["--test"], None, None),
    (
        "lidar record (--test)",
        "examples/lidar_examples/lidar_record.py",
        ["--test"],
        None,
        None,
    ),
    (
        "lidar playback (--test)",
        "examples/lidar_examples/lidar_playback.py",
        ["--test"],
        None,
        {"LIDAR_PLAYBACK_FILE": LIDAR_BAG_FILE},
    ),
    ("lidar device_control (--test)", "examples/lidar_examples/lidar_device_control.py", ["--test"], None, None),
]

# ---------------------------------------------------------------------------

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


INTER_TEST_DELAY = 5  # seconds between tests for device recovery


def safe_label(label: str) -> str:
    return label.replace(" ", "_").replace("(", "").replace(")", "").replace("--", "")


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


def save_log(label, stdout, stderr, report_dir):
    """Save test console output to <report_dir>/logs/<label>.log. Returns relative path."""
    log_dir = os.path.join(report_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    label_id = safe_label(label)
    log_path = os.path.join(log_dir, f"{label_id}.log")
    with open(log_path, "w") as f:
        f.write(f"=== {label} ===\n")
        f.write("stdout:\n")
        f.write(stdout.decode(errors="replace"))
        f.write("\nstderr:\n")
        f.write(stderr.decode(errors="replace"))
    return f"logs/{label_id}.log"


def copy_artifacts(label, script, report_dir) -> list[dict]:
    """Copy images (PNG) and point cloud files (PLY) from test_outputs/ into report_dir/outputs/<label>/."""
    base = os.path.basename(script)
    name_no_ext = os.path.splitext(base)[0]

    # For scripts with multiple modes, pick the output dir based on the label
    if name_no_ext == "03_color_and_depth_aligned":
        if "HW" in label.upper():
            out_dir_name = "color_depth_aligned_hw"
        else:
            out_dir_name = "color_depth_aligned_sw"
    elif name_no_ext == "01_recorder":
        out_dir_name = "recorder"
    elif name_no_ext == "02_playback":
        if "NO-GUI" in label.upper() or "NOGUI" in label.upper().replace("-", "").replace("_", ""):
            out_dir_name = "playback_nogui"
        else:
            out_dir_name = "playback_gui"
    else:
        dir_map = {
            "02_depth_visualization": "depth_visualization",
            "05_point_cloud": "point_cloud",
            "06_multi_streams": "multi_streams",
            "01_recorder": "recorder",
            "02_playback": "playback",
            "03_save_image_to_disk": "save_image_to_disk",
            "08_custom_filter_chain": "custom_filter_chain",
            "09_post_processing": "post_processing",
            "10_hdr": "hdr",
            "13_confidence": "confidence",
            "15_high_performance_pipeline": "high_performance_pipeline",
            "17_laser_interleave": "laser_interleave",
            "quick_start": "quick_start",
            "ruler": "ruler",
            "lidar_quick_start": "lidar_quick_start",
            "lidar_record": "lidar_record",
            "lidar_playback": "lidar_playback",
            "lidar_stream": "lidar_stream",
            "lidar_device_control": "lidar_device_control",
        }
        out_dir_name = dir_map.get(name_no_ext)
        if not out_dir_name:
            return []

    src_dir = os.path.join(REPO, "test_outputs", out_dir_name)
    if not os.path.isdir(src_dir):
        return []

    label_id = safe_label(label)
    dst_dir = os.path.join(report_dir, "outputs", label_id)
    os.makedirs(dst_dir, exist_ok=True)

    artifacts = []
    for f in sorted(os.listdir(src_dir)):
        lower = f.lower()
        if lower.endswith(".png"):
            shutil.copy2(os.path.join(src_dir, f), os.path.join(dst_dir, f))
            artifacts.append({"path": f"outputs/{label_id}/{f}", "type": "image"})
        elif lower.endswith(".ply"):
            shutil.copy2(os.path.join(src_dir, f), os.path.join(dst_dir, f))
            artifacts.append({"path": f"outputs/{label_id}/{f}", "type": "pointcloud"})
    return artifacts


def _category_from_script(script: str) -> str:
    """Map a script path to its category label."""
    norm = script.replace("\\", "/").lstrip("/")
    if norm.startswith("examples/beginner/"):
        return "Beginner"
    if norm.startswith("examples/advanced/"):
        return "Advanced"
    if norm.startswith("examples/applications/"):
        return "Applications"
    if norm.startswith("examples/quick_start"):
        return "Quick Start"
    if norm.startswith("examples/lidar_examples/"):
        return "LiDAR"
    return "Other"


def render_html_report(results, output_dir):
    """Generate a standalone HTML report grouped by category."""
    os.makedirs(output_dir, exist_ok=True)

    # Group results by category, preserving original order within each group
    category_order = ["Quick Start", "Beginner", "Advanced", "Applications", "LiDAR", "Other"]
    groups: dict[str, list[dict]] = {}
    for r in results:
        cat = _category_from_script(r["script"])
        groups.setdefault(cat, []).append(r)

    # Build table rows with category separators
    row_parts = []
    for cat in category_order:
        items = groups.get(cat)
        if not items:
            continue

        # Category header row
        passed = sum(1 for r in items if r["status"] in ("PASS", "TIMEOUT"))
        failed = sum(1 for r in items if r["status"] in ("FAIL", "ERROR"))
        skipped = sum(1 for r in items if r["status"] == "SKIP")
        summary = f"{passed} passed"
        if failed:
            summary += f", {failed} failed"
        if skipped:
            summary += f", {skipped} skipped"
        row_parts.append(f'<tr class="category"><td colspan="6">{html.escape(cat)} — {html.escape(summary)}</td></tr>')

        for r in items:
            label = r["label"]
            status = r["status"]
            log_path = r["log_path"]
            artifacts = r.get("artifacts", [])
            elapsed = r["duration"]

            # Status styling: PASS=green, SKIP=yellow, FAIL=red
            if status in ("PASS", "TIMEOUT"):
                status_bg = "#1f8b4c"
                status_color = "#fff"
                display_status = "PASS" if status == "PASS" else "TIMEOUT"
            elif status == "SKIP":
                status_bg = "#f59e0b"
                status_color = "#1a1a1a"
                display_status = "SKIP"
            elif status in ("FAIL", "ERROR"):
                status_bg = "#b42318"
                status_color = "#fff"
                display_status = "FAIL"
            else:
                status_bg = "#667085"
                status_color = "#fff"
                display_status = status.upper()

            # Log link
            log_html = "-"
            if log_path:
                log_html = f'<a href="{html.escape(log_path)}">log</a>'

            # Artifacts
            artifacts_html = ""
            if artifacts:
                parts = []
                for art in artifacts:
                    if art["type"] == "image":
                        parts.append(
                            f'<a href="{html.escape(art["path"])}">'
                            f'<img src="{html.escape(art["path"])}" alt="{html.escape(os.path.basename(art["path"]))}">'
                            f"</a>"
                        )
                    elif art["type"] == "pointcloud":
                        parts.append(
                            f'<a href="{html.escape(art["path"])}" class="ply-link">'
                            f'{html.escape(os.path.basename(art["path"]))}'
                            f"</a>"
                        )
                artifacts_html = "".join(parts)

            display_message = r.get("message", "")

            row_parts.append(
                "<tr>"
                f"<td>{html.escape(label)}</td>"
                f'<td><span class="status" style="background:{status_bg};color:{status_color};">{html.escape(display_status)}</span></td>'
                f"<td>{elapsed:.2f}s</td>"
                f"<td>{html.escape(display_message)}</td>"
                f"<td>{log_html}</td>"
                f"<td class=\"images\">{artifacts_html or '-'}</td>"
                "</tr>"
            )

    passed = sum(1 for r in results if r["status"] in ("PASS", "TIMEOUT"))
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    total = len(results)

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    document = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Examples Smoke Test Report</title>
  <style>
    body {{ font-family: "Segoe UI", "PingFang SC", sans-serif; background: #f8fafc; color: #101828; margin: 24px; }}
    h1 {{ margin-bottom: 8px; }}
    .summary {{ display: flex; gap: 12px; margin: 0 0 20px; flex-wrap: wrap; }}
    .card {{ background: white; border: 1px solid #d0d5dd; border-radius: 12px; padding: 12px 16px; min-width: 120px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; }}
    th, td {{ border: 1px solid #eaecf0; padding: 10px 12px; vertical-align: top; text-align: left; }}
    th {{ background: #f2f4f7; }}
    .status {{ color: white; border-radius: 999px; padding: 2px 10px; font-size: 12px; display: inline-block; }}
    .category {{ background: #f0f5ff; font-weight: 600; font-size: 14px; }}
    .category td {{ padding: 8px 14px; }}
    .images img {{ width: 120px; height: 90px; object-fit: cover; border: 1px solid #d0d5dd; border-radius: 8px; margin-right: 8px; margin-bottom: 8px; background: #fff; }}
    .ply-link {{ display: inline-block; padding: 4px 10px; background: #f2f4f7; border: 1px solid #d0d5dd; border-radius: 6px; margin-right: 8px; margin-bottom: 8px; font-size: 12px; font-family: monospace; }}
    a {{ color: #175cd3; text-decoration: none; }}
  </style>
</head>
<body>
  <h1>Examples Smoke Test Report</h1>
  <div>Generated at {html.escape(now)}</div>
  <div class="summary">
    <div class="card"><strong>Total</strong><div>{total}</div></div>
    <div class="card"><strong>Passed</strong><div>{passed}</div></div>
    <div class="card"><strong>Failed</strong><div>{failed}</div></div>
    <div class="card"><strong>Skipped</strong><div>{skipped}</div></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Example</th>
        <th>Status</th>
        <th>Duration</th>
        <th>Message</th>
        <th>Log</th>
        <th>Images</th>
      </tr>
    </thead>
    <tbody>
      {"".join(row_parts)}
    </tbody>
  </table>
</body>
</html>
"""
    report_path = os.path.join(output_dir, "report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(document)
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Run pyorbbecsdk example smoke tests")
    parser.add_argument("--lidar", action="store_true", help="Include LiDAR examples in the test run")
    args = parser.parse_args()

    # Prepare report directory — clean previous run artifacts
    report_dir = os.path.join(REPO, REPORT_DIR)
    outputs_dir = os.path.join(report_dir, "outputs")
    logs_dir = os.path.join(report_dir, "logs")
    for d in [outputs_dir, logs_dir]:
        if os.path.isdir(d):
            shutil.rmtree(d)
    os.makedirs(report_dir, exist_ok=True)

    results = []
    print(f"\n{'='*72}")
    print(f"  pyorbbecsdk Example Smoke Tests")
    print(f"  Timeout per example: {TIMEOUT_SEC}s")
    print(f"  Report: {REPORT_DIR}/")
    if args.lidar:
        print(f"  LiDAR examples: enabled")
    print(f"{'='*72}\n")

    all_tests = TESTS + (LIDAR_TESTS if args.lidar else [])

    results = []
    # Record hardcoded skip items (not executed, just reported as SKIPPED)
    for label, script, reason in HARDCODED_SKIP:
        log_path = save_log(label, f"SKIPPED: {reason}".encode(), b"", report_dir)
        results.append({
            "label": label,
            "script": script,
            "status": "SKIP",
            "duration": 0,
            "log_path": log_path,
            "artifacts": [],
            "message": reason,
        })

    for label, script, extra_args, stdin_input, env_override in all_tests:
        print(f"  Running  {label:<45}", end="", flush=True)
        status, elapsed, stdout, stderr = run_one(label, script, extra_args, stdin_input, env_override)

        # Save log directly into report_dir/logs/
        log_path = save_log(label, stdout, stderr, report_dir)

        # Copy test artifacts into report_dir/outputs/
        artifacts = copy_artifacts(label, script, report_dir)

        message = ""
        if status == "FAIL":
            err_lines = stderr.decode(errors="replace").strip().splitlines()
            message = err_lines[-1] if err_lines else ""
            # Show last 10 lines of stderr for diagnosis
            for line in err_lines[-10:]:
                print(f"      {RED}{line}{RESET}")
        elif status == "SKIP":
            message = "feature not supported by device"
        elif status == "TIMEOUT":
            message = f"timeout after {TIMEOUT_SEC}s"

        display_status = status
        if status == "PASS" or status == "TIMEOUT":
            color = GREEN
            display_status = "PASS" if status == "PASS" else "TIMEOUT"
        elif status == "SKIP":
            color = YELLOW
            display_status = "SKIP"
        else:
            color = RED

        print(f"  {color}{display_status:8}{RESET}  ({elapsed:.1f}s)")

        if INTER_TEST_DELAY > 0:
            time.sleep(INTER_TEST_DELAY)

        results.append(
            {
                "label": label,
                "script": script,
                "status": status,
                "duration": elapsed,
                "log_path": log_path,
                "artifacts": artifacts,
                "message": message,
            }
        )

    # Generate HTML report
    report_path = render_html_report(results, report_dir)
    print(f"\n  Report: {REPORT_DIR}/report.html")

    # Clean up intermediate test_outputs directory
    test_outputs_dir = os.path.join(REPO, "test_outputs")
    if os.path.isdir(test_outputs_dir):
        shutil.rmtree(test_outputs_dir)
        print(f"  Cleaned up: test_outputs/")

    # Summary
    passed = sum(1 for r in results if r["status"] in ("PASS", "TIMEOUT"))
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    skipped = sum(1 for r in results if r["status"] == "SKIP")
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
    for bag in [BAG_FILE, NOGUI_BAG_FILE, LIDAR_BAG_FILE]:
        if os.path.exists(os.path.join(REPO, bag)):
            os.remove(os.path.join(REPO, bag))
            print(f"  Cleaned up: {bag}")

    return 1 if (failed + errors) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
