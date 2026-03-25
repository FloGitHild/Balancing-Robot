"""
Stream Connection Tester for ESP32P4
Tests various stream URLs to find the correct one
"""

import cv2
import sys
import time
import requests
from urllib.parse import urljoin

def test_http_stream(url, timeout=5):
    """Test if an HTTP stream URL is accessible"""
    print(f"  Testing {url}...", end=" ", flush=True)
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code < 400:
            print("✅ Accessible")
            return True
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)[:30]}")
        return False

def test_opencv_stream(url, timeout=3):
    """Test if OpenCV can open the stream"""
    print(f"  Testing {url} (OpenCV)...", end=" ", flush=True)
    try:
        cap = cv2.VideoCapture(url)
        # Try to read a frame with timeout
        start = time.time()
        frame_read = False
        while time.time() - start < timeout:
            ret, frame = cap.read()
            if ret:
                frame_read = True
                break
            time.sleep(0.1)
        
        cap.release()
        
        if frame_read:
            print("✅ Stream works!")
            return True
        else:
            print("❌ No frames received")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)[:30]}")
        return False

def main():
    """Test various stream configurations"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  Stream Connection Tester for ESP32P4                         ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    
    # Common localhost URLs
    localhost_urls = [
        'http://localhost:5000/video_feed',
        'http://localhost:5000/video',
        'http://localhost:5000',
        'http://localhost:8000/video_feed',
        'http://localhost:8000/video',
        'http://localhost:8000',
        'http://localhost:8080/video_feed',
        'http://localhost:8080/video',
        'http://localhost:8080',
        'http://127.0.0.1:5000/video_feed',
        'http://127.0.0.1:5000/video',
        'http://127.0.0.1:5000',
    ]
    
    print("🔍 Testing localhost URLs:")
    print("-" * 60)
    working_urls = []
    
    for url in localhost_urls:
        if test_opencv_stream(url):
            working_urls.append(url)
    
    print()
    if working_urls:
        print("✅ Found working stream URL(s):")
        print()
        for i, url in enumerate(working_urls, 1):
            print(f"  {i}. {url}")
        print()
        print("Update Vision Detection.py with one of these URLs:")
        print(f"  STREAM_URL = '{working_urls[0]}'")
    else:
        print("❌ No working stream URLs found")
        print()
        print("Troubleshooting:")
        print("  1. Is the ESP32P4 simulator running?")
        print("  2. Check the network and firewall settings")
        print("  3. Try accessing the URL in your browser")
        print("  4. Check ESP32P4 documentation for the correct endpoint")
    
    print()
    print("Other options to test:")
    print("  • Local video file: STREAM_URL = 'path/to/video.mp4'")
    print("  • Webcam: STREAM_URL = 0")
    print("  • IP camera: STREAM_URL = 'rtsp://camera_ip/stream'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
        sys.exit(0)
