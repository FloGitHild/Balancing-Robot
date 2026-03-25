╔════════════════════════════════════════════════════════════════════════════╗
║              ADVANCED VISION ANALYZER - ESP32P4                            ║
║          Comprehensive Image Analysis & Feature Extraction                 ║
╚════════════════════════════════════════════════════════════════════════════╝

✨ NEW FEATURES (Advanced Version)
═══════════════════════════════════════════════════════════════════════════

This is a fully redesigned vision system with multiple detection engines:

🎯 MULTI-PURPOSE DETECTION:
  ✓ Objects (chairs, trees, plants, animals, persons, vehicles, etc.)
  ✓ Faces (precise face detection + keypoint extraction)
  ✓ Facial landmarks (468-point mesh for detailed analysis)
  ✓ Scene colors (dominant color, brightness, saturation)
  ✓ Edge detection (complexity analysis, scene structure)

🔍 INFORMATION EXTRACTION:
  ✓ Object positions, dimensions, confidence scores
  ✓ Facial keypoints: eyes, nose, mouth, ears coordinates
  ✓ Scene color profile (RGB, HSV analysis)
  ✓ Image complexity and edge density
  ✓ Spatial relationships between objects

⚡ PERFORMANCE OPTIMIZED:
  ✓ Configurable FPS (default: 5 FPS, range: 1-10 FPS)
  ✓ Automatic frame skipping to reduce processing
  ✓ Lightweight YOLOv8-nano model
  ✓ MediaPipe for efficient face/landmark detection
  ✓ Much lower computational load than real-time systems


📋 SUPPORTED DETECTIONS
═══════════════════════════════════════════════════════════════════════════

OBJECTS (via YOLOv8):
  └─ Persons, pets, furniture:
     • person, dog, cat, bird, horse, sheep, cow, zebra, giraffe
  └─ Furniture & structures:
     • chair, couch, table, bed, laptop, monitor, furniture, bench
  └─ Nature:
     • tree (implied via plant detection), potted plant, backpack
  └─ Vehicles & transport:
     • bicycle, car, motorcycle, bus, truck, train, airplane, boat
  └─ Food & objects:
     • banana, apple, bottle, cup, plate, bowl, utensils

FACES (via MediaPipe):
  ├─ Face detection (bounding boxes + confidence)
  ├─ Facial keypoints:
  │  • Right Eye, Left Eye
  │  • Nose, Mouth
  │  • Right Ear, Left Ear
  └─ Facial landmarks (468 points per face)
     • Precise contours for eyes, eyebrows, lips, jawline
     • Iris and pupil tracking
     • Face outline and geometry

SCENE ANALYSIS:
  ├─ Dominant color detection
  ├─ Brightness and saturation
  ├─ Edge density (scene complexity)
  └─ Overall image complexity classification


🚀 QUICK START
═══════════════════════════════════════════════════════════════════════════

1. Install dependencies (first time only):
   pip install -r Lokal\requirements_vision.txt

2. Run the advanced analyzer:
   python Lokal\"Vision Detection.py"

3. Check TERMINAL OUTPUT for comprehensive analysis each frame


📊 TERMINAL OUTPUT EXAMPLE
═══════════════════════════════════════════════════════════════════════════

================================================================================
[14:23:45.123] 🔍 COMPREHENSIVE IMAGE ANALYSIS
================================================================================

📊 SCENE ANALYSIS:
  • Dominant Color: GREEN (Hue: 85°)
  • Brightness: 145/255
  • Saturation: 120/255
  • Complexity: High (Edge Density: 18.5%)

📦 OBJECTS DETECTED (3):
  • person
    └─ Confidence: 94% | Position: (640, 360) | Size: 120×180px
  • chair
    └─ Confidence: 87% | Position: (400, 400) | Size: 80×140px
  • potted plant
    └─ Confidence: 82% | Position: (200, 450) | Size: 60×100px

👤 FACES DETECTED (1):
  Face #1:
    • Confidence: 96%
    • Position: (640, 280)
    • Size: 100×120px
    • Keypoints detected: 6
    • Key locations:
      - right_eye: (620, 270)
      - left_eye: (660, 270)
      - nose: (640, 290)
      - mouth: (640, 310)
      - right_ear: (590, 260)
      - left_ear: (690, 260)

🧬 FACIAL LANDMARKS (1 faces with mesh):
  Face #0: 468 landmark points

================================================================================


⚙️ CONFIGURATION
═══════════════════════════════════════════════════════════════════════════

Edit Vision Detection.py to customize:

STREAM_URL = 'http://localhost:5000/video_feed'
  └─ Where to get the video feed
     • ESP32P4 webstream URL
     • Local video: 'path/to/video.mp4'
     • Webcam: 0

TARGET_FPS = 5
  └─ How many analysis frames per second (1-10)
     • 5 FPS = analyze 5 frames per second = 0.2s latency
     • 1 FPS = slower but lower CPU usage
     • 10 FPS = more frequent analysis but higher CPU

CONFIDENCE_THRESHOLD = 0.5
  └─ Minimum detection confidence (0.0 - 1.0)
     • 0.5 = only detect if 50%+ confident
     • Lower = more detections (more false positives)
     • Higher = fewer detections (might miss objects)

MODEL_SIZE = 'n'
  └─ YOLOv8 model size
     • 'n' = nano (lightest, fastest) ← Recommended for analysis
     • 's', 'm', 'l' = progressively larger/slower


🎮 INTERACTIVE CONTROLS
═══════════════════════════════════════════════════════════════════════════

While analysis is running:

Q  - Quit the program
S  - Save current analysis frame with overlays
D  - Toggle display window (useful if terminal mode only)


💡 USAGE PATTERNS
═══════════════════════════════════════════════════════════════════════════

PATTERN 1: Continuous Surveillance
┌─────────────────────────────────┐
│ Run at 5 FPS                    │
│ Analyzes every 6th frame        │
│ ~0.2 second latency             │
│ Low CPU usage                   │
│ Logs to terminal                │
└─────────────────────────────────┘

PATTERN 2: High-Detail Analysis
┌─────────────────────────────────┐
│ Reduce TARGET_FPS to 1-2        │
│ More time per analysis          │
│ Better for complex scenes       │
│ Slowest CPU usage               │
│ Most detailed output            │
└─────────────────────────────────┘

PATTERN 3: Fast Reaction
┌─────────────────────────────────┐
│ Increase TARGET_FPS to 10       │
│ Minimal latency                 │
│ Higher CPU usage                │
│ Real-time responsiveness        │
│ Use 'n' model size              │
└─────────────────────────────────┘


📈 DATA STRUCTURE
═══════════════════════════════════════════════════════════════════════════

Each frame analysis includes:

OBJECTS (YOLOv8 Detection):
{
  'type': 'object',
  'class': 'person',              # Object class name
  'confidence': 0.94,              # Detection confidence 0-1
  'x1': 580, 'y1': 280,           # Top-left corner
  'x2': 700, 'y2': 460,           # Bottom-right corner
  'center_x': 640,                 # Center X coordinate
  'center_y': 370,                 # Center Y coordinate
  'width': 120, 'height': 180      # Bounding box dimensions
}

FACES (MediaPipe Detection):
{
  'type': 'face',
  'confidence': 0.96,              # Face detection confidence
  'center_x': 640, 'center_y': 280, # Face center
  'width': 100, 'height': 120,     # Face dimensions
  'keypoints': 6,                  # Number of detected keypoints
  'keypoint_coords': {             # Facial keypoint positions
    'right_eye': {'x': 620, 'y': 270},
    'left_eye': {'x': 660, 'y': 270},
    'nose': {'x': 640, 'y': 290},
    'mouth': {'x': 640, 'y': 310},
    'right_ear': {'x': 590, 'y': 260},
    'left_ear': {'x': 690, 'y': 260}
  }
}

SCENE ANALYSIS (Colors):
{
  'dominant_color': 'GREEN',       # Color name
  'dominant_hue': 85,              # HSV hue (0-180)
  'brightness': 145,               # 0-255 scale
  'saturation': 120                # Color intensity 0-255
}

SCENE ANALYSIS (Edges):
{
  'edge_density': 18.5,            # Percentage of edges
  'complexity': 'High'             # Low/Medium/High
}

FACIAL LANDMARKS (Mesh):
{
  'face_id': 0,                    # Which face (0=first)
  'num_landmarks': 468,            # Always 468 points
  'landmarks': [                   # Array of all landmarks
    {'x': 0.5, 'y': 0.3, 'z': 0.1}, # Normalized coordinates
    ...
  ]
}


🔬 ADVANCED USAGE
═══════════════════════════════════════════════════════════════════════════

CAPTURE SPECIFIC FACE COORDINATES:

from Vision Detection import AdvancedVisionAnalyzer

analyzer = AdvancedVisionAnalyzer()
cap = analyzer.connect_stream()

ret, frame = cap.read()
faces = analyzer.detect_faces(frame)
formatted_faces = analyzer.format_face_detection(faces, frame.shape)

for face in formatted_faces:
    print(f"Face at: {face['center_x']}, {face['center_y']}")
    for kp_name, kp_pos in face['keypoint_coords'].items():
        print(f"  {kp_name}: {kp_pos}")


TRACK OBJECTS BETWEEN FRAMES:

# Store positions from previous frame
previous_objects = {}

for frame in stream:
    current_objects = get_detections(frame)
    
    # Match current objects to previous
    for obj in current_objects:
        # Find closest object in previous frame
        best_match = find_nearest(obj, previous_objects)
        
        # Calculate movement
        if best_match:
            dx = obj['center_x'] - best_match['center_x']
            dy = obj['center_y'] - best_match['center_y']
            print(f"Movement: ({dx}, {dy})")
    
    previous_objects = current_objects


🔧 TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════

Problem: "faces not detected"
  → Ensure good lighting
  → Try increasing detection window (face must be ~50px+)
  → Lower CONFIDENCE_THRESHOLD to 0.3-0.4

Problem: "objects not detected but faces are"
  → Different detection engine - faces are more robust
  → Check object confidence threshold
  → Verify objects are in COCO dataset

Problem: "ModuleNotFoundError: mediapipe"
  → Install: pip install mediapipe>=0.10.0
  → Or: pip install -r requirements_vision.txt

Problem: "Low FPS, laggy analysis"
  → Increase TARGET_FPS delay: TARGET_FPS = 1-2
  → Use MODEL_SIZE = 'n'
  → Close other applications

Problem: "No faces detected in 'face detection' mode"
  → Ensure faces are frontally oriented
  → Check minimum face size (~50-60 pixels minimum)
  → Try lowering confidence threshold


📚 MODEL INFORMATION
═══════════════════════════════════════════════════════════════════════════

YOLOv8-nano:
  • Size: ~6 MB (compact)
  • Speed: ⚡⚡⚡ Very fast
  • Accuracy: ★★★ Good
  • Classes: 80 (COCO dataset)
  • GPU memory: ~400MB

MediaPipe Face Detection:
  • Size: ~20 MB
  • Speed: ⚡⚡⚡⚡ Excellent
  • Accuracy: ★★★★★ Excellent for faces
  • Performance: Works on mobile devices

MediaPipe Face Mesh:
  • Size: ~8 MB
  • Speed: ⚡⚡⚡⚡ Excellent
  • Landmarks: 468 points per face
  • Real-time capable


🎯 REAL-WORLD EXAMPLES
═══════════════════════════════════════════════════════════════════════════

1. ROBOT SURVEILLANCE:
   - Detect persons entering robot area
   - Track face landmarks for orientation
   - Avoid obstacles (chairs, plants)
   - React to color changes (red alert?)

2. ROOM MONITORING:
   - Continuous 1-5 FPS analysis
   - Count people in room
   - Detect furniture changes
   - Track person movements

3. WILDLIFE MONITORING:
   - Detect animals (dogs, cats, birds)
   - Identify plants/trees
   - Analyze scene color/brightness
   - Long-term statistics

4. SECURITY:
   - Guard duty (face detection)
   - Perimeter monitoring (person + vehicle)
   - Scene analysis (lighting changes)
   - Alert on unusual activity


═══════════════════════════════════════════════════════════════════════════
Advanced Vision Analyzer - Ready for Production ✅
═══════════════════════════════════════════════════════════════════════════
