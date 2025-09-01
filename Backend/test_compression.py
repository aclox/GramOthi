#!/usr/bin/env python3
"""
Compression and bandwidth testing script for GramOthi
Tests audio compression, image compression, and network simulation
"""

import os
import sys
import time
import requests
import tempfile
from pathlib import Path
import json
from PIL import Image
import numpy as np

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.compression_service import CompressionService, BandwidthDetector

class NetworkSimulator:
    """Simulate different network conditions for testing."""
    
    NETWORK_PROFILES = {
        "2g": {
            "download_speed": 50,  # kbps
            "upload_speed": 20,   # kbps
            "latency": 300,       # ms
            "description": "2G Network - Very slow"
        },
        "3g": {
            "download_speed": 200,  # kbps
            "upload_speed": 100,   # kbps
            "latency": 150,        # ms
            "description": "3G Network - Slow"
        },
        "4g": {
            "download_speed": 1000,  # kbps
            "upload_speed": 500,    # kbps
            "latency": 50,          # ms
            "description": "4G Network - Fast"
        },
        "wifi": {
            "download_speed": 5000,  # kbps
            "upload_speed": 2000,   # kbps
            "latency": 20,          # ms
            "description": "WiFi Network - Very fast"
        }
    }
    
    @staticmethod
    def simulate_download_time(file_size_mb: float, network_profile: str) -> float:
        """Simulate download time for a file on different networks."""
        profile = NetworkSimulator.NETWORK_PROFILES.get(network_profile, NetworkSimulator.NETWORK_PROFILES["3g"])
        download_speed_kbps = profile["download_speed"]
        
        # Convert MB to KB and calculate time
        file_size_kb = file_size_mb * 1024
        download_time_seconds = file_size_kb / download_speed_kbps
        
        return download_time_seconds

class CompressionTester:
    """Test compression functionality and performance."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = tempfile.mkdtemp()
    
    def create_test_audio(self, duration_seconds: int = 10) -> str:
        """Create a test audio file using ffmpeg."""
        output_path = os.path.join(self.temp_dir, "test_audio.wav")
        
        # Generate a simple sine wave audio file
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={duration_seconds}",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            "-y",  # Overwrite output file
            output_path
        ]
        
        try:
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return output_path
            else:
                print(f"Failed to create test audio: {result.stderr}")
                return None
        except Exception as e:
            print(f"Error creating test audio: {e}")
            return None
    
    def create_test_image(self, width: int = 1920, height: int = 1080) -> str:
        """Create a test image file."""
        output_path = os.path.join(self.temp_dir, "test_image.jpg")
        
        # Create a test image with some content
        image = Image.new('RGB', (width, height), color='white')
        
        # Add some content to make it compressible
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        # Add text
        text = "GramOthi Test Image\nLow-Bandwidth Optimization\nRural Education Platform"
        draw.text((50, 50), text, fill='black', font=font)
        
        # Add some shapes
        draw.rectangle([100, 200, 400, 300], fill='blue', outline='red', width=3)
        draw.ellipse([500, 200, 700, 400], fill='green', outline='purple', width=3)
        
        image.save(output_path, 'JPEG', quality=95)
        return output_path
    
    def test_audio_compression(self):
        """Test audio compression across different bandwidth profiles."""
        print("🎵 Testing Audio Compression...")
        
        # Create test audio file
        audio_path = self.create_test_audio(10)  # 10 seconds
        if not audio_path:
            print("❌ Failed to create test audio file")
            return
        
        original_size = CompressionService.get_file_size_mb(audio_path)
        print(f"   Original audio size: {original_size:.2f} MB")
        
        for profile in ["ultra_low", "low", "medium", "high"]:
            compressed_path = os.path.join(self.temp_dir, f"audio_{profile}.mp3")
            
            start_time = time.time()
            success = CompressionService.compress_audio(audio_path, compressed_path, profile)
            compression_time = time.time() - start_time
            
            if success:
                compressed_size = CompressionService.get_file_size_mb(compressed_path)
                compression_ratio = CompressionService.get_compression_ratio(audio_path, compressed_path)
                
                # Simulate download times
                original_download_time = NetworkSimulator.simulate_download_time(original_size, "3g")
                compressed_download_time = NetworkSimulator.simulate_download_time(compressed_size, "3g")
                time_saved = original_download_time - compressed_download_time
                
                result = {
                    "type": "audio",
                    "profile": profile,
                    "original_size_mb": round(original_size, 2),
                    "compressed_size_mb": round(compressed_size, 2),
                    "compression_ratio": round(compression_ratio, 2),
                    "compression_time": round(compression_time, 2),
                    "download_time_saved": round(time_saved, 2),
                    "success": True
                }
                
                print(f"   ✅ {profile}: {compressed_size:.2f} MB ({compression_ratio:.1f}% compression)")
                print(f"      Download time saved: {time_saved:.1f}s on 3G")
            else:
                result = {
                    "type": "audio",
                    "profile": profile,
                    "success": False
                }
                print(f"   ❌ {profile}: Compression failed")
            
            self.test_results.append(result)
    
    def test_image_compression(self):
        """Test image compression across different bandwidth profiles."""
        print("\n🖼️  Testing Image Compression...")
        
        # Create test image file
        image_path = self.create_test_image(1920, 1080)
        if not image_path:
            print("❌ Failed to create test image file")
            return
        
        original_size = CompressionService.get_file_size_mb(image_path)
        print(f"   Original image size: {original_size:.2f} MB")
        
        for profile in ["ultra_low", "low", "medium", "high"]:
            compressed_path = os.path.join(self.temp_dir, f"image_{profile}.jpg")
            
            start_time = time.time()
            success = CompressionService.compress_image(image_path, compressed_path, profile)
            compression_time = time.time() - start_time
            
            if success:
                compressed_size = CompressionService.get_file_size_mb(compressed_path)
                compression_ratio = CompressionService.get_compression_ratio(image_path, compressed_path)
                
                # Simulate download times
                original_download_time = NetworkSimulator.simulate_download_time(original_size, "3g")
                compressed_download_time = NetworkSimulator.simulate_download_time(compressed_size, "3g")
                time_saved = original_download_time - compressed_download_time
                
                result = {
                    "type": "image",
                    "profile": profile,
                    "original_size_mb": round(original_size, 2),
                    "compressed_size_mb": round(compressed_size, 2),
                    "compression_ratio": round(compression_ratio, 2),
                    "compression_time": round(compression_time, 2),
                    "download_time_saved": round(time_saved, 2),
                    "success": True
                }
                
                print(f"   ✅ {profile}: {compressed_size:.2f} MB ({compression_ratio:.1f}% compression)")
                print(f"      Download time saved: {time_saved:.1f}s on 3G")
            else:
                result = {
                    "type": "image",
                    "profile": profile,
                    "success": False
                }
                print(f"   ❌ {profile}: Compression failed")
            
            self.test_results.append(result)
    
    def test_bandwidth_detection(self):
        """Test bandwidth detection logic."""
        print("\n🌐 Testing Bandwidth Detection...")
        
        test_cases = [
            ("Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)", "2g", "ultra_low"),
            ("Mozilla/5.0 (Linux; Android 10; SM-G975F)", "3g", "low"),
            ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "4g", "medium"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "wifi", "high"),
        ]
        
        for user_agent, connection_type, expected_profile in test_cases:
            detected_profile = BandwidthDetector.detect_bandwidth_profile(user_agent, connection_type)
            success = detected_profile == expected_profile
            
            result = {
                "type": "bandwidth_detection",
                "user_agent": user_agent[:50] + "...",
                "connection_type": connection_type,
                "expected_profile": expected_profile,
                "detected_profile": detected_profile,
                "success": success
            }
            
            if success:
                print(f"   ✅ {connection_type}: Correctly detected as {detected_profile}")
            else:
                print(f"   ❌ {connection_type}: Expected {expected_profile}, got {detected_profile}")
            
            self.test_results.append(result)
    
    def test_api_endpoints(self, base_url: str = "http://localhost:8000"):
        """Test API endpoints with different bandwidth profiles."""
        print("\n🔗 Testing API Endpoints...")
        
        # Test bandwidth info endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/media/bandwidth-info", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Bandwidth info endpoint working")
                print(f"      Available profiles: {list(data.get('compression_profiles', {}).keys())}")
            else:
                print(f"   ❌ Bandwidth info endpoint failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Bandwidth info endpoint failed: {e}")
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        print("\n" + "="*60)
        print("📊 COMPRESSION TEST REPORT")
        print("="*60)
        
        # Summary statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Audio compression summary
        audio_tests = [r for r in self.test_results if r.get("type") == "audio" and r.get("success")]
        if audio_tests:
            print(f"\n🎵 Audio Compression Results:")
            for test in audio_tests:
                print(f"   {test['profile']}: {test['compression_ratio']:.1f}% compression, "
                      f"{test['download_time_saved']:.1f}s saved on 3G")
        
        # Image compression summary
        image_tests = [r for r in self.test_results if r.get("type") == "image" and r.get("success")]
        if image_tests:
            print(f"\n🖼️  Image Compression Results:")
            for test in image_tests:
                print(f"   {test['profile']}: {test['compression_ratio']:.1f}% compression, "
                      f"{test['download_time_saved']:.1f}s saved on 3G")
        
        # Bandwidth detection summary
        detection_tests = [r for r in self.test_results if r.get("type") == "bandwidth_detection"]
        if detection_tests:
            successful_detections = sum(1 for r in detection_tests if r.get("success"))
            print(f"\n🌐 Bandwidth Detection: {successful_detections}/{len(detection_tests)} correct")
        
        # Save detailed results
        report_path = os.path.join(self.temp_dir, "compression_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Cleanup
        import shutil
        shutil.rmtree(self.temp_dir)
        
        return self.test_results

def main():
    """Run all compression tests."""
    print("🚀 GramOthi Compression Testing Suite")
    print("="*60)
    
    tester = CompressionTester()
    
    # Run tests
    tester.test_audio_compression()
    tester.test_image_compression()
    tester.test_bandwidth_detection()
    tester.test_api_endpoints()
    
    # Generate report
    results = tester.generate_report()
    
    # Check if all tests passed
    failed_tests = [r for r in results if not r.get("success", False)]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} tests failed. Check the report for details.")
        return 1
    else:
        print(f"\n🎉 All tests passed! Compression system is working correctly.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
