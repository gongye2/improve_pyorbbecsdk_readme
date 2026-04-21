# ******************************************************************************
#  pyorbbecsdk Advanced Example 07 — Per-Frame Metadata
#
#  What you will learn:
#    1. How to read per-frame metadata: exposure time, gain, and timestamp
#    2. How to check which metadata keys are supported by the connected device
#    3. How to display metadata values alongside the live depth stream
#
#  Device requirement: All
#
#  Run:
#    python examples/advanced/07_metadata.py
# ******************************************************************************
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyorbbecsdk import Context, OBError, OBFrameMetadataType, Pipeline  # type: ignore

ESC_KEY = 27


def main():
    parser = argparse.ArgumentParser(description="Per-Frame Metadata")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: collect a few frames of metadata and exit",
    )
    args = parser.parse_args()

    if args.test:
        print("Test mode: collecting metadata for 5 frames then exiting")

    # Check if device is connected
    ctx = Context()
    device_list = ctx.query_devices()
    if device_list.get_count() == 0:
        print("Device Not Found! Please connect an Orbbec camera and try again.")
        return

    # Initialize Pipeline
    pipeline = Pipeline()
    # Start Pipeline
    try:
        pipeline.start()
        print("Pipeline started.")
    except OBError as e:
        print(f"Error: {e}")
        print("Please connect an Orbbec camera and try again.")
        return

    frame_counter = 0
    metadata_frames = 0

    while True:
        try:
            # Get frameSet from Pipeline
            frame_set = pipeline.wait_for_frames(1000)
            if frame_set is None:
                continue

            frame_counter += 1

            for i in range(len(frame_set)):
                frame = frame_set[i]
                print(f"Frame #{frame_counter}, type: {frame.get_type()}")
                metadata_types = [
                    getattr(OBFrameMetadataType, attr)
                    for attr in dir(OBFrameMetadataType)
                    if not attr.startswith("__") and isinstance(getattr(OBFrameMetadataType, attr), OBFrameMetadataType)
                ]

                for metadata_type in metadata_types:
                    if frame.has_metadata(metadata_type):
                        metadata_value = frame.get_metadata_value(metadata_type)
                        print(f"  Metadata type: {metadata_type.name}, value: {metadata_value}")

            metadata_frames += 1

            if args.test and metadata_frames >= 5:
                print(f"Collected metadata for {metadata_frames} frames, exiting test mode.")
                break

        except KeyboardInterrupt:
            break
        except Exception as e:
            print("An error occurred:", e)
            break

    pipeline.stop()
    print("Pipeline stopped.")


if __name__ == "__main__":
    main()
