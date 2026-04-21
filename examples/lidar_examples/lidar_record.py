# ******************************************************************************
#  pyorbbecsdk LiDAR Example — LiDAR Recording
#
#  What you will learn:
#    1. How to record LiDAR point cloud streams to a .bag file
#    2. How to select the recording duration and output path
#    3. How to verify the recording by checking the frame count
#
#  Device requirement: Orbbec LiDAR devices
#
#  Run:
#    python examples/lidar_examples/lidar_record.py
# ******************************************************************************
import argparse
import os
import sys
import threading
import time

from pyorbbecsdk import Config, Context, Pipeline, RecordDevice  # type: ignore

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import is_lidar_device


def select_device(device_list):
    dev_count = device_list.get_count()
    print("Device list: ")
    for i in range(dev_count):
        print(
            f"{i}. name: {device_list.get_device_name_by_index(i)}, "
            f"vid: 0x{hex(device_list.get_device_vid_by_index(i))}, "
            f"pid: 0x{hex(device_list.get_device_pid_by_index(i))}, "
            f"uid: {device_list.get_device_uid_by_index(i)}, "
            f"sn: {device_list.get_device_serial_number_by_index(i)}"
        )

    while True:
        try:
            dev_index = int(input("Select a device index: "))
            if 0 <= dev_index < dev_count:
                return device_list.get_device_by_index(dev_index)
        except ValueError:
            pass
        print("Invalid selection, please reselect.")


def main():
    parser = argparse.ArgumentParser(description="LiDAR Recording")
    parser.add_argument("--test", action="store_true", help="Test mode: record for 5 seconds then exit")
    args = parser.parse_args()

    try:
        ctx = Context()
        device_list = ctx.query_devices()
        if device_list.get_count() < 1:
            print("No device found! Please connect a supported device and retry.")
            return

        if device_list.get_count() == 1:
            device = device_list.get_device_by_index(0)
        else:
            device = select_device(device_list)

        if not is_lidar_device(device):
            print("Invalid device, please connect a LiDAR device!")
            sys.exit(77)

        print("\n" + "-" * 72)

        if args.test:
            file_path = "test_outputs/lidar_record/test_lidar.bag"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            print(f"Test mode: recording to '{file_path}'")
        else:
            file_path = input("Please enter the output filename (with .bag extension): ").strip()
            if not file_path.endswith(".bag"):
                file_path += ".bag"

        pipe = Pipeline(device)
        config = Config()
        sensor_list = device.get_sensor_list()

        for i in range(sensor_list.get_count()):
            sensor = sensor_list.get_sensor_by_index(i)
            sensor_type = sensor.get_type()
            config.enable_stream(sensor_type)

        frame_mutex = threading.Lock()
        frame_count_map = {}

        def on_new_frame(frame_set):
            if frame_set is None:
                return
            with frame_mutex:
                for i in range(frame_set.get_count()):
                    frame = frame_set.get_frame_by_index(i)
                    if frame:
                        f_type = frame.get_type()
                        frame_count_map[f_type] = frame_count_map.get(f_type, 0) + 1

        record_device = RecordDevice(device, file_path)

        pipe.start(config, on_new_frame)

        print("Streams and recorder have started!")
        print("Press Ctrl+C to stop recording and exit safely.")
        print("IMPORTANT: Always exit safely to avoid bag file corruption.\n")

        start_time = time.time() * 1000
        wait_interval = 1000

        try:
            while True:
                time.sleep(0.05)
                current_time = time.time() * 1000

                if current_time > start_time + wait_interval:
                    temp_count_map = {}
                    duration = 0

                    with frame_mutex:
                        current_time = time.time() * 1000
                        duration = current_time - start_time
                        if frame_count_map:
                            start_time = current_time
                            wait_interval = 2000
                            temp_count_map = frame_count_map.copy()
                            for k in frame_count_map:
                                frame_count_map[k] = 0

                    if not temp_count_map:
                        print("Recording... Current FPS: 0")
                    else:
                        fps_info = []
                        for f_type, count in temp_count_map.items():
                            rate = count / (duration / 1000.0)
                            fps_info.append(f"{f_type.name}={rate:.2f}")
                        print(f"Recording... Current FPS: {', '.join(fps_info)}")

                if args.test and (time.time() * 1000 - start_time) > 5000:
                    print("\nTest mode: 5 seconds elapsed, stopping recording.")
                    break

        except KeyboardInterrupt:
            print("\nStopping recording...")

        pipe.stop()
        record_device = None
        print("Recording saved safely.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
