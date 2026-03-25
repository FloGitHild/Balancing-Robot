"""
Quick Live Stream Test
Tests connecting to ESP32P4 simulator and getting one frame
"""

import cv2
import sys

def test_live_stream():
    """Test connecting to the live ESP32P4 stream"""
    print("🧪 Testing Live ESP32P4 Stream Connection...")

    try:
        # Try to connect to the stream
        print("  📡 Connecting to http://localhost:5000/video_feed...")
        cap = cv2.VideoCapture('http://localhost:5000/video_feed')

        if not cap.isOpened():
            print("  ❌ Failed to open stream")
            return False

        print("  ✅ Stream opened successfully")

        # Try to read one frame
        ret, frame = cap.read()
        if ret and frame is not None:
            height, width = frame.shape[:2]
            print(f"  ✅ Frame received: {width}x{height} pixels")
            print("  🎯 Vision detection system is ready!")
        else:
            print("  ❌ No frame received")

        cap.release()
        return ret

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run the live stream test"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         Live ESP32P4 Stream Test                               ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()

    if test_live_stream():
        print("\n✅ ESP32P4 stream is working!")
        print("🎯 Ready to run: python \"Vision Detection.py\"")
    else:
        print("\n❌ Stream test failed")
        print("💡 Make sure ESP32P4 Simulator is running on port 5000")

if __name__ == "__main__":
    main()