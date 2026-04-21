# ******************************************************************************
#  pyorbbecsdk LiDAR Example — LiDAR Stream Viewer
#
#  What you will learn:
#    1. How to stream LiDAR point cloud data continuously
#    2. How to visualize the LiDAR point cloud in real time
#    3. How to display frame rate and point count statistics
#
#  Device requirement: Orbbec LiDAR devices
#
#  Run:
#    python examples/lidar_examples/lidar_stream.py
# ******************************************************************************
import argparse
import os
import sys
import time

import numpy as np

from pyorbbecsdk import OBFormat  # type: ignore
from pyorbbecsdk import (
    Config,
    Context,
    OBFrameAggregateOutputMode,
    OBFrameType,
    OBPropertyID,
    OBSensorType,
    Pipeline,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import is_lidar_device

ESC_KEY = 27
frame_count = 0


def select_device(device_list):
    dev_count = device_list.get_count()
    print("Device list: ")
    for i in range(dev_count):
        print(
            f"{i}. name: {device_list.get_device_name_by_index(i)}, "
            f"vid: 0x{hex(device_list.get_device_vid_by_index(i))}, "
            f"pid: 0x{hex(device_list.get_device_pid_by_index(i))}, "
            f"sn: {device_list.get_device_serial_number_by_index(i)}"
        )

    while True:
        try:
            input_str = input("Select a device index: ")
            dev_index = int(input_str)
            if 0 <= dev_index < dev_count:
                return device_list.get_device_by_index(dev_index)
        except ValueError:
            pass
        print("Invalid selection, please reselect.")


def select_sensors(device):
    selected_sensors = []
    while True:
        print("Sensor list: ")
        sensor_list = device.get_sensor_list()
        count = sensor_list.get_count()
        for index in range(0, count):
            sensor_type = sensor_list.get_sensor_by_index(index).get_type()
            print(f" - {index}.sensor type: {sensor_type}")

        print(f" - {count}.all sensors")
        print(f"Select a sensor to enable (input sensor index, '{count}' to select all sensors): ")

        try:
            sensor_selected = int(input())
        except:
            print("Invalid input, please enter a number!")
            continue

        if sensor_selected > count or sensor_selected < 0:
            if sensor_selected == -1:
                break
            else:
                print("Invalid input, please reselect the sensor!")
                continue

        if sensor_selected == count:
            for index in range(0, count):
                sensor = sensor_list.get_sensor_by_index(index)
                selected_sensors.append(sensor)
        else:
            sensor = sensor_list.get_sensor_by_index(sensor_selected)
            selected_sensors.append(sensor)
        break

    return selected_sensors


def select_streams(device, config):
    selected_sensors = select_sensors(device)
    if not selected_sensors:
        print("No sensor selected")
        return

    for sensor in selected_sensors:
        stream_profile_list = sensor.get_stream_profile_list()
        count = stream_profile_list.get_count()
        if count == 0:
            print(f"No stream profile found for sensor: {sensor.get_type()}")

        print(f"Stream profile list for sensor: {sensor.get_type()}")
        for index in range(0, count):
            profile = stream_profile_list.get_stream_profile_by_index(index)
            if sensor.get_type() == OBSensorType.ACCEL_SENSOR:
                acc_rate = profile.get_sample_rate()
                print(f" - {index}.acc rate: {acc_rate}")

            elif sensor.get_type() == OBSensorType.GYRO_SENSOR:
                gyro_rate = profile.get_sample_rate()
                print(f" - {index}.gyro rate: {gyro_rate}")

            elif sensor.get_type() == OBSensorType.LIDAR_SENSOR:
                lidar_profile = profile.as_lidar_stream_profile()
                format_name = profile.get_format()
                scan_rate = profile.get_scan_rate()
                print(f" - {index}.format: {format_name}, scan rate: {scan_rate}")

            else:
                continue

        print("Select a stream profile to enable (input stream profile index): ")
        while True:
            stream_profile_selected = int(input())
            if stream_profile_selected >= count or stream_profile_selected < -1:
                print("Invalid input, please reselect the stream profile!")
                continue
            if stream_profile_selected == -1:
                break

            selected_stream_profile = stream_profile_list.get_stream_profile_by_index(stream_profile_selected)
            config.enable_stream(selected_stream_profile)
            break


def print_imu_value(frame, unit_str):
    data = frame.get_value()
    frame_type = frame.get_type()
    type_str = "Accel" if frame_type == OBFrameType.ACCEL_FRAME else "Gyro"

    print(f"frame index: {frame.get_index()}")
    print(
        f"{type_str} Frame: \n{{\n"
        f"  tsp = {frame.get_timestamp_us()}\n"
        f"  temperature = {frame.get_temperature()}\n"
        f"  {type_str}.x = {data.x}{unit_str}\n"
        f"  {type_str}.y = {data.y}{unit_str}\n"
        f"  {type_str}.z = {data.z}{unit_str}\n"
        f"}}\n"
    )


def print_lidar_point_cloud_info(frame):
    point_format = frame.get_format()
    if point_format not in [
        OBFormat.LIDAR_SPHERE_POINT,
        OBFormat.LIDAR_POINT,
        OBFormat.LIDAR_SCAN,
    ]:
        print("LiDAR point cloud format invalid")
        return

    min_point_value = 1e-6
    valid_point_count = 0
    data = frame.get_data()

    if point_format == OBFormat.LIDAR_SPHERE_POINT:
        points = np.frombuffer(
            data,
            dtype=[
                ("distance", "f4"),
                ("theta", "f4"),
                ("phi", "f4"),
                ("reflectivity", "u1"),
                ("tag", "u1"),
            ],
        )

        dist = points["distance"]
        theta_rad = np.radians(points["theta"])
        phi_rad = np.radians(points["phi"])

        cos_phi = np.cos(phi_rad)
        x = dist * np.cos(theta_rad) * cos_phi
        y = dist * np.sin(theta_rad) * cos_phi
        z = dist * np.sin(phi_rad)

        mask = (dist >= min_point_value) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        valid_point_count = np.sum(mask)

    elif point_format == OBFormat.LIDAR_POINT:
        points = np.frombuffer(
            data,
            dtype=[
                ("x", "f4"),
                ("y", "f4"),
                ("z", "f4"),
                ("reflectivity", "u1"),
                ("tag", "u1"),
            ],
        )
        x, y, z = points["x"], points["y"], points["z"]
        mask = (np.abs(z) >= min_point_value) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        valid_point_count = np.sum(mask)

    elif point_format == OBFormat.LIDAR_SCAN:
        points = np.frombuffer(data, dtype=[("angle", "f4"), ("distance", "f4"), ("intensity", "u2")])

        dist = points["distance"]
        angle_rad = np.radians(points["angle"])

        x = dist * np.cos(angle_rad)
        y = dist * np.sin(angle_rad)

        mask = (dist >= min_point_value) & np.isfinite(x) & np.isfinite(y)
        valid_point_count = np.sum(mask)

    if valid_point_count == 0:
        print("LiDAR point cloud vertices is zero")
        return

    print(f"frame index: {frame.get_index()}")
    print(
        f"LiDAR PointCloud Frame: \n{{\n"
        f"  tsp = {frame.get_timestamp_us()}\n"
        f"  format = {point_format}\n"
        f"  valid point count = {valid_point_count}\n"
        f"}}\n"
    )


def on_new_frame_set(frames):
    global frame_count
    if frames is None:
        return

    for i in range(frames.get_count()):
        frame = frames.get_frame_by_index(i)
        if frame is None:
            continue

        if frame_count % 50 == 0:
            f_type = frame.get_type()
            if f_type == OBFrameType.LIDAR_POINTS_FRAME:
                print_lidar_point_cloud_info(frame.as_lidar_points_frame())
            elif f_type == OBFrameType.ACCEL_FRAME:
                print_imu_value(frame.as_accel_frame(), "m/s^2")
            elif f_type == OBFrameType.GYRO_FRAME:
                print_imu_value(frame.as_gyro_frame(), "rad/s")

    frame_count += 1


def main():
    parser = argparse.ArgumentParser(description="LiDAR Stream Viewer")
    parser.add_argument("--test", action="store_true", help="Test mode: auto-select sensor, capture frames, exit")
    args = parser.parse_args()

    try:
        pipe = None
        ctx = Context()
        device_list = ctx.query_devices()

        if device_list.get_count() <= 0:
            print("Device Not Found")
            return

        device = None
        if device_list.get_count() == 1:
            device = device_list.get_device_by_index(0)
        else:
            device = select_device(device_list)

        if not is_lidar_device(device):
            print("Invalid device, please connect a LiDAR device!")
            sys.exit(77)

        pipe = Pipeline(device)
        config = Config()

        dev_info = device.get_device_info()
        print("-" * 50)
        print(
            f"Current Device: name: {dev_info.get_name()}, VID: {hex(dev_info.get_vid())}, PID: {hex(dev_info.get_pid())}, "
            f"UID: {dev_info.get_uid()}, Serial Number: {dev_info.get_serial_number()}, Connection Type: {dev_info.get_connection_type()}"
        )

        try:
            ip_address = device.get_device_info().get_device_ip_address()
            print(f"LiDAR IP Address: {ip_address}")
        except:
            print("Could not read LiDAR IP Address")

        device.set_int_property(OBPropertyID.OB_PROP_LIDAR_TAIL_FILTER_LEVEL_INT, 0)

        if args.test:
            # Test mode: enable all sensors automatically
            sensor_list = device.get_sensor_list()
            for i in range(sensor_list.get_count()):
                sensor = sensor_list.get_sensor_by_index(i)
                config.enable_stream(sensor.get_type())
        else:
            select_streams(device, config)

        config.set_frame_aggregate_output_mode(OBFrameAggregateOutputMode.FULL_FRAME_REQUIRE)

        pipe.start(config, on_new_frame_set)

        print("The stream is started!")
        print("Press Ctrl+C to exit!\n")

        if args.test:
            # Collect a fixed number of frames then exit
            target_frames = 5
            while True:
                time.sleep(1)
                if frame_count >= target_frames:
                    print(f"Collected {frame_count} frames in test mode, exiting.")
                    break
        else:
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if pipe is not None:
            pipe.stop()


if __name__ == "__main__":
    main()
