# ******************************************************************************
#  pyorbbecsdk LiDAR Example — LiDAR Quick Start
#
#  What you will learn:
#    1. How to detect and connect to an Orbbec LiDAR device
#    2. How to enable the LiDAR point cloud stream
#    3. How to capture LiDAR frames and save the point cloud to a .ply file
#
#  Device requirement: Orbbec LiDAR devices (e.g., Gemini 2 XL with LiDAR)
#
#  Run:
#    python examples/lidar_examples/lidar_quick_start.py
# ******************************************************************************
import argparse
import os
import sys

from pyorbbecsdk import OBError, Pipeline, save_lidar_point_cloud_to_ply  # type: ignore

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import is_lidar_device

ESC_KEY = 27

save_points_dir = os.path.join(os.getcwd(), "point_clouds")
if not os.path.exists(save_points_dir):
    os.mkdir(save_points_dir)


def main():
    parser = argparse.ArgumentParser(description="LiDAR Quick Start")
    parser.add_argument("--test", action="store_true", help="Test mode: auto-save frames and exit")
    args = parser.parse_args()

    if args.test:
        os.makedirs(save_points_dir, exist_ok=True)
        print(f"Test mode: saving LiDAR point clouds to '{save_points_dir}/'")

    # Create a pipeline.
    pipeline = Pipeline()

    # Get the device from pipeline.
    device = pipeline.get_device()

    # Check LiDAR device
    if not is_lidar_device(device):
        print("Invalid device, please connect a LiDAR device!")
        sys.exit(77)

    # Start the pipeline with default config.
    # Modify the default configuration by the configuration file: "*SDKConfig.xml"
    pipeline.start()

    print("LiDAR stream is started!")
    print("Press 'r' or 'R' to create LiDAR PointCloud and save to ply file! ")
    print("Press 'q' or 'Q' to exit! ")

    test_frame_count = 0

    try:
        while True:
            if args.test:
                # Wait for LiDAR frame automatically
                frames = pipeline.wait_for_frames(1000)
                if frames is None:
                    continue
                frame = frames.get_lidar_points_frame()
                if frame is None:
                    continue
                save_path = os.path.join(save_points_dir, f"lidar_frame_{test_frame_count:04d}.ply")
                save_lidar_point_cloud_to_ply(save_path, frame, False)
                test_frame_count += 1
                print(f"[Saved] {save_path}")
                if test_frame_count >= 3:
                    print(f"Saved {test_frame_count} LiDAR point clouds, exiting test mode.")
                    break
            else:
                # Wait for user input
                key = input("Wating for command:")
                if key.lower() == "q":
                    break

                # Press 'r' or 'R' to save LiDAR point cloud to ply file
                if key.lower() == "r":
                    print("Save LiDAR PointCloud to ply file, this will take some time...")

                    # Wait for frameSet from the pipeline, the default timeout is 1000ms.
                    frames = pipeline.wait_for_frames(1000)
                    if frames is None:
                        print("No frame data, please try again!")
                        continue

                    # Get LiDAR point cloud frame
                    frame = frames.get_lidar_points_frame()
                    if frame is None:
                        print("No LiDAR frame found!")
                        continue

                    # Save point cloud data to ply file
                    save_path = os.path.join(save_points_dir, "LiDARPoints.ply")
                    save_lidar_point_cloud_to_ply(save_path, frame, False)
                    print(f"LiDARPoints.ply Saved at: {os.path.abspath(save_path)}")

    except KeyboardInterrupt:
        pass
    except OBError as e:
        print(e)
    finally:
        # Stop the Pipeline, no frame data will be generated
        pipeline.stop()


if __name__ == "__main__":
    main()
