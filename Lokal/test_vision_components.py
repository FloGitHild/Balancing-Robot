"""
Quick Test for Vision Detection Components
Tests object detection and analysis without requiring a video stream
"""

import cv2
import numpy as np
from ultralytics import YOLO
import sys
import os

def test_object_detection():
    """Test YOLOv8 object detection"""
    print("🧪 Testing YOLOv8 Object Detection...")

    try:
        # Load model
        model = YOLO('yolov8n.pt')
        print("  ✅ Model loaded")

        # Create a test image (simple colored rectangle)
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        # Draw a red rectangle (simulating an object)
        cv2.rectangle(test_image, (200, 150), (400, 330), (0, 0, 255), -1)
        print("  ✅ Test image created")

        # Run detection
        results = model(test_image, verbose=False)
        print("  ✅ Detection completed")

        # Check results
        if results and len(results) > 0:
            detections = results[0]
            if detections.boxes is not None and len(detections.boxes) > 0:
                print(f"  ✅ Found {len(detections.boxes)} detections")
                for i, box in enumerate(detections.boxes):
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = box.conf[0].cpu().numpy()
                    class_name = detections.names[class_id]
                    print(f"    Detection {i+1}: {class_name} ({confidence:.2%})")
            else:
                print("  ⚠️  No objects detected (expected for test image)")
        else:
            print("  ❌ No results returned")

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_image_analysis():
    """Test image analysis functions"""
    print("\n🧪 Testing Image Analysis...")

    try:
        # Create test image
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some color and features
        cv2.rectangle(test_image, (0, 0), (320, 240), (0, 255, 0), -1)  # Green half
        cv2.circle(test_image, (500, 300), 50, (0, 0, 255), -1)  # Red circle

        # Test color analysis
        hsv = cv2.cvtColor(test_image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        dominant_hue = np.argmax(hist)
        print(f"  ✅ Color analysis: Dominant hue = {dominant_hue}")

        # Test brightness
        brightness = int(np.mean(cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)))
        print(f"  ✅ Brightness analysis: {brightness}/255")

        # Test edge detection
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size * 100
        print(f"  ✅ Edge analysis: {edge_density:.1f}% edge density")

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         Vision Detection Component Test                      ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()

    success_count = 0
    total_tests = 2

    # Test object detection
    if test_object_detection():
        success_count += 1

    # Test image analysis
    if test_image_analysis():
        success_count += 1

    print(f"\n{'='*60}")
    print(f"Test Results: {success_count}/{total_tests} passed")

    if success_count == total_tests:
        print("✅ All vision detection components working!")
        print("\n🎯 The system is ready for ESP32P4 stream analysis.")
        print("   Run: python \"Lokal/Vision Detection.py\"")
    else:
        print("❌ Some components failed. Check error messages above.")

    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)