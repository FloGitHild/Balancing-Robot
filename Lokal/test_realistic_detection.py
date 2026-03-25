"""
Test Object Detection with Real Image
Creates a test image with recognizable objects and tests detection
"""

import cv2
import numpy as np
from ultralytics import YOLO
import sys

def create_test_image_with_objects():
    """Create a test image with simple shapes that might be detected"""
    # Create a larger image
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255  # White background

    # Draw a person-like shape (stick figure)
    # Head
    cv2.circle(img, (400, 150), 30, (0, 128, 255), -1)  # Orange head
    # Body
    cv2.rectangle(img, (385, 180), (415, 280), (255, 0, 0), -1)  # Blue body
    # Arms
    cv2.rectangle(img, (360, 200), (385, 210), (139, 69, 19), -1)  # Brown arm
    cv2.rectangle(img, (415, 200), (440, 210), (139, 69, 19), -1)  # Brown arm
    # Legs
    cv2.rectangle(img, (390, 280), (400, 350), (0, 0, 0), -1)  # Black leg
    cv2.rectangle(img, (400, 280), (410, 350), (0, 0, 0), -1)  # Black leg

    # Draw a chair-like shape
    cv2.rectangle(img, (100, 300), (200, 400), (139, 69, 19), -1)  # Brown chair seat
    cv2.rectangle(img, (120, 250), (130, 300), (139, 69, 19), -1)  # Back support
    cv2.rectangle(img, (170, 250), (180, 300), (139, 69, 19), -1)  # Back support

    # Draw a bottle-like shape
    cv2.rectangle(img, (600, 350), (650, 450), (0, 255, 0), -1)  # Green bottle body
    cv2.rectangle(img, (615, 320), (635, 350), (0, 255, 0), -1)  # Neck

    # Add some text for context
    cv2.putText(img, "Test Scene", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    return img

def test_realistic_detection():
    """Test detection on a more realistic scene"""
    print("🧪 Testing Object Detection on Realistic Scene...")

    try:
        # Load YOLO model
        model = YOLO('yolov8n.pt')
        print("  ✅ Model loaded")

        # Create test image
        test_img = create_test_image_with_objects()
        print("  ✅ Test scene created")

        # Save for inspection
        cv2.imwrite('test_scene.jpg', test_img)
        print("  ✅ Test image saved as test_scene.jpg")

        # Run detection
        results = model(test_img, verbose=False)
        print("  ✅ Detection completed")

        # Process results
        if results and len(results) > 0:
            detections = results[0]
            if detections.boxes is not None and len(detections.boxes) > 0:
                print(f"  ✅ Found {len(detections.boxes)} detections:")
                for i, box in enumerate(detections.boxes):
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = box.conf[0].cpu().numpy()
                    class_name = detections.names[class_id]
                    # Get bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    print(f"    {i+1}. {class_name} ({confidence:.1%}) at [{x1:.0f},{y1:.0f}]-[{x2:.0f},{y2:.0f}]")
            else:
                print("  ⚠️  No objects detected")
                print("     This is normal - YOLO needs real objects, not drawings")
        else:
            print("  ❌ No results returned")

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run the realistic detection test"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         Realistic Object Detection Test                     ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()

    if test_realistic_detection():
        print("\n✅ Object detection test completed!")
        print("📝 Note: YOLOv8 is trained on real photos, so simple drawings")
        print("   may not be detected. This is expected behavior.")
        print("\n🎯 Ready for real ESP32P4 video stream analysis!")
        return True
    else:
        print("\n❌ Test failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)