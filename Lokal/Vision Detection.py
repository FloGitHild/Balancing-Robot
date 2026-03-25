"""
Advanced Vision Analyzer for ESP32P4 Webstream
Comprehensive Image Analysis: Objects, Faces, Features, Scene Understanding
"""

import cv2
import numpy as np
from ultralytics import YOLO
import threading
import time
from datetime import datetime
from collections import deque
import sys
import os
import json
from pathlib import Path
import torch

# MediaPipe may be unavailable in restricted environments; handle gracefully
mp = None
mediapipe_available = False
try:
    import mediapipe as mp
    mediapipe_available = True
except ImportError:
    print("⚠️  MediaPipe not available: face detection/landmarks disabled")

# Configuration
STREAM_URL = 'http://localhost:5000/video_feed'
MODEL_FILE = 'yolov8-face.pt'  # Dedicated face detection model
OBJECT_MODEL_FILE = 'yolov8n.pt'  # Object detection model (lightweight)
CONFIDENCE_THRESHOLD = 0.1  # Lower threshold for more detections (can be adjusted)
FACE_CONFIDENCE_THRESHOLD = 0.30  # More tolerant threshold for faces
TARGET_FPS = 5  # 1-10 FPS is enough for continuous analysis
MAX_HISTORY = 30

DETECT_EVERY_N_FRAMES = 2  # Only detect objects every N frames for performance

# Color mappings for detected objects
CLASS_COLORS = {
    'person': (0, 255, 0),
    'bicycle': (255, 0, 0),
    'car': (0, 0, 255),
    'dog': (255, 192, 203),
    'cat': (165, 42, 42),
    'chair': (75, 0, 130),
    'plant': (0, 128, 0),
    'tree': (34, 139, 34),
    'face': (0, 255, 255),
}

class FaceDatabase:
    """Manage face detection and storage"""
    
    def __init__(self, database_dir='face_database'):
        """Initialize face database"""
        self.database_dir = Path(database_dir)
        self.database_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.database_dir / 'faces_metadata.json'
        self.faces_dir = self.database_dir / 'faces'
        self.faces_dir.mkdir(exist_ok=True)
        
        # Load existing metadata
        self.metadata = self._load_metadata()
        
        print(f"✅ Face Database initialized at: {self.database_dir.absolute()}")
    
    def _load_metadata(self):
        """Load metadata from file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def save_face(self, frame, face_data, face_name=None):
        """
        Save a detected face to the database
        
        Args:
            frame: The video frame
            face_data: Dictionary with face detection info (x1, y1, x2, y2, etc.)
            face_name: Optional name, if None will prompt user
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        # Extract face ROI
        x1, y1, x2, y2 = face_data['x1'], face_data['y1'], face_data['x2'], face_data['y2']
        face_roi = frame[y1:y2, x1:x2]
        
        if face_roi.size == 0:
            print("❌ Invalid face region")
            return False
        
        # Get face name from user
        if face_name is None:
            try:
                face_name = input("\n👤 Enter name for this face: ").strip()
            except EOFError:
                print("⚠️  Could not read input, skipping face save")
                return False
            
            if not face_name:
                print("⚠️  Empty name, skipping face save")
                return False
        
        # Sanitize name for filename
        safe_name = "".join(c for c in face_name if c.isalnum() or c in (' ', '-', '_')).strip()
        
        # Create person directory
        person_dir = self.faces_dir / safe_name
        person_dir.mkdir(exist_ok=True)
        
        # Save face image with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        face_filename = f"{safe_name}_{timestamp}.jpg"
        face_path = person_dir / face_filename
        
        cv2.imwrite(str(face_path), face_roi)
        
        # Update metadata
        if safe_name not in self.metadata:
            self.metadata[safe_name] = {
                'name': face_name,
                'faces': [],
                'created_at': datetime.now().isoformat()
            }
        
        self.metadata[safe_name]['faces'].append({
            'filename': face_filename,
            'timestamp': timestamp,
            'confidence': face_data['confidence'],
            'size': f"{face_data['width']}x{face_data['height']}",
            'saved_at': datetime.now().isoformat()
        })
        
        self._save_metadata()
        
        print(f"✅ Face saved: {face_path}")
        print(f"   Name: {face_name} | Size: {face_data['width']}×{face_data['height']}px | Confidence: {face_data['confidence']:.1%}")
        
        return True
    
    def get_face_count(self, person_name=None):
        """Get count of faces in database"""
        if person_name:
            return len(self.metadata.get(person_name, {}).get('faces', []))
        return sum(len(p.get('faces', [])) for p in self.metadata.values())
    
    def list_people(self):
        """List all people in database"""
        return list(self.metadata.keys())

class AdvancedVisionAnalyzer:
    """Advanced vision analyzer with multi-modal detection"""
    
    def __init__(self):
        """Initialize all vision models"""
        print("🚀 Initializing Advanced Vision Analyzer...")
        
        # Try to load dedicated face detection model, fallback to nano object detection
        print("  👤 Loading Face Detection model...")
        try:
            self.face_model = YOLO(MODEL_FILE)
            self.use_dedicated_face_model = True
            print(f"    ✅ Loaded dedicated face model: {MODEL_FILE}")
        except Exception as e:
            print(f"    ⚠️  Dedicated face model not found ({e})")
            print(f"    📦 Falling back to object detection model...")
            self.face_model = YOLO('yolov8n.pt')
            self.use_dedicated_face_model = False
        
        # Set model to GPU if available for better performance
        if torch.cuda.is_available():
            self.face_model = self.face_model.cuda()
            print("    ⚡ GPU acceleration enabled")
        else:
            print("    ℹ️  GPU not available, using CPU")
        
        # Object detection model (lightweight nano version)
        print("  📦 Loading Object Detection model...")
        self.object_model = YOLO(OBJECT_MODEL_FILE)
        if torch.cuda.is_available():
            self.object_model = self.object_model.cuda()
        
        # Initialize timing for FPS control
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()
        self.running = False
        self.frame_skip = max(1, int(30 / TARGET_FPS))
        self.frame_index = 0
        self.detection_frame_counter = 0  # For throttling detections
        
        # Cache for detections
        self.last_object_detections = None  # Initialize as None, not empty list
        self.last_object_detection_time = 0
        
        # Initialize face database
        self.face_database = FaceDatabase()
        self.last_saved_face_time = 0
        self.face_save_cooldown = 0.5
        self.faces_to_collect = 10
        self.detected_faces = {}
        self.face_id_counter = 0
        
        print("✅ All models loaded successfully!")
    
    def connect_stream(self):
        """Connect to webstream"""
        print(f"📡 Connecting to webstream at {STREAM_URL}...")
        cap = cv2.VideoCapture(STREAM_URL)
        
        if not cap.isOpened():
            print(f"❌ Failed to connect to {STREAM_URL}")
            print("   Trying alternative URLs...")
            
            alternatives = [
                'http://localhost:8000/video',
                'http://localhost:8080/video',
                'http://127.0.0.1:5000/video_feed',
            ]
            
            for alt_url in alternatives:
                cap = cv2.VideoCapture(alt_url)
                if cap.isOpened():
                    print(f"✅ Connected to {alt_url}")
                    return cap
            
            return None
        
        print("✅ Connected to webstream!")
        return cap
    
    def detect_objects(self, frame):
        """Detect objects using YOLOv8 (throttled for performance)"""
        # Only detect objects every N frames to improve performance
        self.detection_frame_counter += 1
        if self.detection_frame_counter % DETECT_EVERY_N_FRAMES != 0:
            # Return cached results or empty results if not yet detected
            if self.last_object_detections is not None:
                return self.last_object_detections
            else:
                # Return a dummy results object with no boxes for first frames
                results = self.object_model(frame, verbose=False)
                return results[0]  # Still do first detection
        
        results = self.object_model(frame, verbose=False)
        self.last_object_detections = results[0]
        return results[0]
    
    def detect_faces(self, frame):
        """Detect faces using dedicated face model or fallback to person head region."""
        faces = []

        # Dedicated face model path
        if self.use_dedicated_face_model:
            results = self.face_model(frame, verbose=False, conf=FACE_CONFIDENCE_THRESHOLD)
            if results[0].boxes is None or len(results[0].boxes) == 0:
                return []

            for box in results[0].boxes:
                confidence = float(box.conf[0].cpu().numpy())
                if confidence >= FACE_CONFIDENCE_THRESHOLD:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    faces.append({'x1': int(x1), 'y1': int(y1), 'x2': int(x2), 'y2': int(y2), 'confidence': confidence})
            return faces

        # Fallback path: use person detections from object model and crop top 45%
        results = self.object_model(frame, verbose=False)
        if results[0].boxes is None or len(results[0].boxes) == 0:
            return []

        for box in results[0].boxes:
            class_id = int(box.cls[0].cpu().numpy())
            class_name = results[0].names[class_id].lower()
            if class_name in ['person', 'human']:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                face_height = max(20, int((y2 - y1) * 0.45))
                y2_face = min(y2, y1 + face_height)
                confidence = float(box.conf[0].cpu().numpy())
                if confidence >= FACE_CONFIDENCE_THRESHOLD:
                    faces.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2_face, 'confidence': confidence})
        return faces
    
    def extract_face_landmarks(self, frame):
        """Extract detailed facial landmarks"""
        # MediaPipe landmarks not available, returning empty
        return []
    
    def analyze_colors(self, frame):
        """Analyze dominant colors in the image"""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Calculate histogram
        hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        
        # Find dominant hue
        dominant_hue = np.argmax(hist)
        
        # Map hue to color name
        if dominant_hue < 10 or dominant_hue > 170:
            dominant_color = "RED"
        elif 10 <= dominant_hue < 25:
            dominant_color = "ORANGE"
        elif 25 <= dominant_hue < 35:
            dominant_color = "YELLOW"
        elif 35 <= dominant_hue < 80:
            dominant_color = "GREEN"
        elif 80 <= dominant_hue < 100:
            dominant_color = "CYAN"
        elif 100 <= dominant_hue < 125:
            dominant_color = "BLUE"
        elif 125 <= dominant_hue < 170:
            dominant_color = "PURPLE"
        else:
            dominant_color = "UNKNOWN"
        
        # Calculate overall brightness
        brightness = int(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))
        
        # Calculate saturation
        saturation = int(np.mean(hsv[:, :, 1]))
        
        return {
            'dominant_color': dominant_color,
            'dominant_hue': int(dominant_hue),
            'brightness': brightness,
            'saturation': saturation
        }
    
    def analyze_edges(self, frame):
        """Detect edges for scene complexity analysis"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size * 100
        return {
            'edge_density': round(edge_density, 2),
            'complexity': 'Low' if edge_density < 5 else ('Medium' if edge_density < 15 else 'High')
        }
    
    def format_object_detection(self, result):
        """Format YOLOv8 detection results"""
        detections = []
        
        # Handle None or empty results
        if result is None or result.boxes is None or len(result.boxes) == 0:
            return detections
        
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            confidence = box.conf[0].cpu().numpy()
            class_id = int(box.cls[0].cpu().numpy())
            class_name = result.names[class_id]
            
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            width = int(x2 - x1)
            height = int(y2 - y1)
            
            if confidence >= CONFIDENCE_THRESHOLD:
                detections.append({
                    'type': 'object',
                    'class': class_name,
                    'confidence': float(confidence),
                    'x1': int(x1),
                    'y1': int(y1),
                    'x2': int(x2),
                    'y2': int(y2),
                    'center_x': center_x,
                    'center_y': center_y,
                    'width': width,
                    'height': height
                })
        
        return detections
    
    def format_face_detection(self, face_detections, frame_shape):
        """Format face detection results with size filtering"""
        faces = []
        h, w, _ = frame_shape

        for detection in face_detections:
            if isinstance(detection, dict):
                x1, y1, x2, y2 = detection['x1'], detection['y1'], detection['x2'], detection['y2']
                confidence = detection.get('confidence', 0.0)
            else:
                x1, y1, x2, y2 = detection.xyxy[0].cpu().numpy()
                confidence = float(detection.conf[0].cpu().numpy())

            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            width = x2 - x1
            height = y2 - y1

            if confidence >= FACE_CONFIDENCE_THRESHOLD and width >= 20 and height >= 20:
                faces.append({
                    'type': 'face',
                    'class': 'face',
                    'name': detection.get('name', 'Unknown') if isinstance(detection, dict) else 'Unknown',
                    'confidence': float(confidence),
                    'x1': x1,
                    'y1': y1,
                    'x2': x2,
                    'y2': y2,
                    'center_x': center_x,
                    'center_y': center_y,
                    'width': width,
                    'height': height,
                    'keypoints': 0,
                    'keypoint_coords': {}
                })

        return faces
    
    def _extract_keypoints(self, detection, w, h):
        """Extract facial keypoint coordinates"""
        keypoints = {}
        keypoint_names = ['right_eye', 'left_eye', 'nose', 'mouth', 'right_ear', 'left_ear']
        
        for i, kp in enumerate(detection.location_data.relative_keypoints[:min(6, len(detection.location_data.relative_keypoints))]):
            if i < len(keypoint_names):
                keypoints[keypoint_names[i]] = {
                    'x': int(kp.x * w),
                    'y': int(kp.y * h)
                }
        
        return keypoints
    
    def format_facial_landmarks(self, landmarks_list):
        """Format facial landmark mesh data"""
        landmarks = []
        
        for face_idx, face_landmarks in enumerate(landmarks_list):
            landmark_points = []
            
            # The new API has landmarks as a list of normalized coordinates
            for landmark in face_landmarks:
                landmark_points.append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z if hasattr(landmark, 'z') else 0.0
                })
            
            landmarks.append({
                'face_id': face_idx,
                'num_landmarks': len(landmark_points),
                'landmarks': landmark_points
            })
        
        return landmarks
    
    def print_comprehensive_analysis(self, detections, faces, landmarks, color_info, edge_info, timestamp):
        """Print comprehensive analysis to terminal"""
        print(f"\n{'='*80}")
        print(f"[{timestamp}] 🔍 COMPREHENSIVE IMAGE ANALYSIS")
        print(f"{'='*80}")
        
        # Scene Analysis
        print(f"\n📊 SCENE ANALYSIS:")
        print(f"  • Dominant Color: {color_info['dominant_color']} (Hue: {color_info['dominant_hue']}°)")
        print(f"  • Brightness: {color_info['brightness']}/255")
        print(f"  • Saturation: {color_info['saturation']}/255")
        print(f"  • Complexity: {edge_info['complexity']} (Edge Density: {edge_info['edge_density']}%)")
        
        # Object Detection
        if detections:
            print(f"\n📦 OBJECTS DETECTED ({len(detections)}):")
            for det in detections:
                print(f"  • {det['class'].upper()}")
                print(f"    └─ Confidence: {det['confidence']:.1%} | Position: ({det['center_x']}, {det['center_y']}) | Size: {det['width']}×{det['height']}px")
        else:
            print(f"\n📦 OBJECTS: None detected")
        
        # Face Detection
        if faces:
            print(f"\n👤 FACES DETECTED ({len(faces)}):")
            for i, face in enumerate(faces, 1):
                print(f"  Face #{i}:")
                print(f"    • Confidence: {face['confidence']:.1%}")
                print(f"    • Position: ({face['center_x']}, {face['center_y']})")
                print(f"    • Size: {face['width']}×{face['height']}px")
                print(f"    • Keypoints detected: {face['keypoints']}")
                if face['keypoint_coords']:
                    print(f"    • Key locations:")
                    for kp_name, kp_pos in face['keypoint_coords'].items():
                        print(f"      - {kp_name}: ({kp_pos['x']}, {kp_pos['y']})")
        else:
            print(f"\n👤 FACES: None detected")
        
        # Facial Landmarks
        if landmarks:
            print(f"\n🧬 FACIAL LANDMARKS ({len(landmarks)} faces with mesh):")
            for landmark in landmarks:
                print(f"  Face #{landmark['face_id']}: {landmark['num_landmarks']} landmark points")
        
        print(f"\n{'='*80}\n")
    
    def draw_analysis_overlay(self, frame, detections, faces):
        """Draw analysis results on frame"""
        # Draw objects
        for det in detections:
            color = CLASS_COLORS.get(det['class'], (255, 255, 255))
            cv2.rectangle(frame, (det['x1'], det['y1']), (det['x2'], det['y2']), color, 2)
            
            label = f"{det['class']} {det['confidence']:.0%}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            
            (text_width, text_height) = cv2.getTextSize(label, font, font_scale, thickness)[0]
            cv2.rectangle(frame,
                         (det['x1'], det['y1'] - text_height - 5),
                         (det['x1'] + text_width + 5, det['y1']),
                         color, -1)
            cv2.putText(frame, label,
                       (det['x1'] + 2, det['y1'] - 3),
                       font, font_scale, (0, 0, 0), thickness)
            
            # Center dot
            cv2.circle(frame, (det['center_x'], det['center_y']), 3, color, -1)
        
        # Draw faces
        for face in faces:
            color = CLASS_COLORS['face']
            cv2.rectangle(frame, (face['x1'], face['y1']), (face['x2'], face['y2']), color, 2)
            
            # Show name with confidence
            person_name = face.get('name', 'Unknown')
            label = f"{person_name} {face['confidence']:.0%}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            
            (text_width, text_height) = cv2.getTextSize(label, font, font_scale, 1)[0]
            cv2.rectangle(frame,
                         (face['x1'], face['y1'] - text_height - 5),
                         (face['x1'] + text_width + 5, face['y1']),
                         color, -1)
            cv2.putText(frame, label,
                       (face['x1'] + 2, face['y1'] - 3),
                       font, font_scale, (0, 0, 0), 1)
            
            # Draw keypoints
            for kp_name, kp_pos in face['keypoint_coords'].items():
                cv2.circle(frame, (kp_pos['x'], kp_pos['y']), 2, color, -1)
        
        return frame
    
    def handle_face_detection(self, frame, face_list):
        """
        Handle newly detected faces - automatically saves 5-10 images per person
        
        Args:
            frame: Current video frame
            face_list: List of detected faces
        """
        current_time = time.time()
        
        for i, face in enumerate(face_list):
            # Only process high-confidence faces
            if face['confidence'] < 0.6:
                continue
            
            # Cooldown to prevent saving identical frames too quickly
            if current_time - self.last_saved_face_time < self.face_save_cooldown:
                continue
            
            face_id = f"face_{i}"
            
            # First time seeing this face position - ask for name
            if face_id not in self.detected_faces:
                try:
                    person_name = input(f"\n👤 New face detected! Enter name (or press Enter to skip): ").strip()
                    
                    if not person_name:
                        print("⏭️  Skipping this face")
                        continue
                    
                    self.detected_faces[face_id] = {
                        'name': person_name,
                        'count': 0,
                        'first_seen': current_time
                    }
                    
                    print(f"\n🆕 Starting to collect images for: {person_name}")
                    print(f"   Target: {self.faces_to_collect} images")
                    
                except EOFError:
                    continue
            
            # Check if we've already collected enough images for this person
            face_data = self.detected_faces[face_id]
            if face_data['count'] >= self.faces_to_collect:
                continue
            
            # Save the face automatically
            person_name = face_data['name']
            if self.face_database.save_face(frame, face, face_name=person_name):
                face_data['count'] += 1
                self.last_saved_face_time = current_time
                
                saved_count = self.face_database.get_face_count(person_name)
                remaining = max(0, self.faces_to_collect - face_data['count'])
                
                print(f"   ✅ Image {face_data['count']}/{self.faces_to_collect} for {person_name} | Total in DB: {saved_count} | Remaining: {remaining}")
                
                # Celebrate when we have enough images
                if face_data['count'] >= self.faces_to_collect:
                    print(f"\n🎉 Collected {self.faces_to_collect} images for {person_name}! Ready for recognition.\n")
            
            # Clean up old entries
            if current_time - face_data['first_seen'] > 120:  # 2 minutes timeout
                if face_data['count'] > 0:
                    del self.detected_faces[face_id]
    
    def calculate_fps(self):
        """Calculate frames per second"""
        self.frame_count += 1
        current_time = time.time()
        time_diff = current_time - self.last_time
        
        if time_diff >= 1.0:
            self.fps = self.frame_count / time_diff
            self.frame_count = 0
            self.last_time = current_time
    
    def run(self):
        """Main analysis loop"""
        cap = self.connect_stream()
        
        if cap is None:
            print("❌ Could not connect to video stream")
            return
        
        self.running = True
        show_display = True
        frame_save_counter = 0
        
        print(f"\n✅ Starting vision analysis at ~{TARGET_FPS} FPS...")
        print("📚 Press 'q' to quit, 's' to save frame, 'd' to toggle display")
        print("=" * 80)
        
        try:
            while self.running:
                ret, frame = cap.read()
                
                if not ret:
                    print("❌ Failed to read frame")
                    break
                
                # Frame skipping to maintain target FPS
                self.frame_index += 1
                if self.frame_index % self.frame_skip != 0:
                    continue
                
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # Run all detections
                object_result = self.detect_objects(frame)
                object_detections = self.format_object_detection(object_result)
                
                face_detections = self.detect_faces(frame)
                face_list = self.format_face_detection(face_detections, frame.shape)
                
                face_landmarks = self.extract_face_landmarks(frame)
                landmarks = self.format_facial_landmarks(face_landmarks)
                
                # Analyze image properties
                color_analysis = self.analyze_colors(frame)
                edge_analysis = self.analyze_edges(frame)
                
                # Print comprehensive analysis
                self.print_comprehensive_analysis(
                    object_detections,
                    face_list,
                    landmarks,
                    color_analysis,
                    edge_analysis,
                    timestamp
                )
                
                # Handle face detection and saving
                self.handle_face_detection(frame, face_list)
                
                # Update face names from detected_faces tracking
                for i, face in enumerate(face_list):
                    face_id = f"face_{i}"
                    if face_id in self.detected_faces:
                        face['name'] = self.detected_faces[face_id]['name']
                
                # Calculate FPS
                self.calculate_fps()
                
                # Draw and display
                if show_display:
                    display_frame = self.draw_analysis_overlay(
                        frame.copy(),
                        object_detections,
                        face_list
                    )
                    
                    # Add info overlay
                    info = f"FPS: {self.fps:.1f} | Objects: {len(object_detections)} | Faces: {len(face_list)}"
                    cv2.putText(display_frame, info, (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    cv2.imshow('Advanced Vision Analyzer', display_frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n👋 Quitting...")
                        break
                    elif key == ord('s'):
                        frame_save_counter += 1
                        filename = f"analysis_frame_{frame_save_counter}_{int(time.time())}.jpg"
                        cv2.imwrite(filename, display_frame)
                        print(f"✅ Frame saved: {filename}")
                    elif key == ord('d'):
                        show_display = False
                        print("🔇 Display disabled (terminal mode only)")
                
        except KeyboardInterrupt:
            print("\n⏸️  Interrupted by user")
        finally:
            self.running = False
            cap.release()
            cv2.destroyAllWindows()
            print("✅ Analysis complete, stream closed")


def main():
    """Main entry point"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  Advanced Vision Analyzer for ESP32P4                          ║")
    print("║  Objects, Faces, Landmarks, Colors, Edge Detection             ║")
    print("║  Comprehensive Image Analysis (1-10 FPS)                       ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    analyzer = AdvancedVisionAnalyzer()
    analyzer.run()


if __name__ == "__main__":
    main()
