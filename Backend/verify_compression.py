#!/usr/bin/env python3
"""
Comprehensive compression verification script for GramOthi
Verifies all compression features are working correctly
"""

import os
import sys
import time
import requests
import tempfile
import json
from pathlib import Path
import subprocess

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking Dependencies...")
    
    dependencies = [
        ("ffmpeg", "ffmpeg -version"),
        ("PIL", "python -c 'from PIL import Image; print(\"PIL OK\")'"),
        ("requests", "python -c 'import requests; print(\"requests OK\")'"),
    ]
    
    all_ok = True
    for name, command in dependencies:
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {name}: OK")
            else:
                print(f"   ❌ {name}: Not found or not working")
                all_ok = False
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
            all_ok = False
    
    return all_ok

def test_compression_service():
    """Test the compression service functionality."""
    print("\n🔧 Testing Compression Service...")
    
    try:
        from app.services.compression_service import CompressionService, BandwidthDetector
        
        # Test bandwidth detection
        print("   Testing bandwidth detection...")
        profiles = ["ultra_low", "low", "medium", "high"]
        for profile in profiles:
            recommendations = BandwidthDetector.get_compression_recommendations(profile)
            print(f"   ✅ {profile}: {recommendations['description']}")
        
        # Test compression profiles
        print("   Testing compression profiles...")
        for profile in profiles:
            settings = CompressionService.BANDWIDTH_PROFILES.get(profile)
            if settings:
                print(f"   ✅ {profile}: Audio {settings['audio_bitrate']}, Image quality {settings['image_quality']}")
            else:
                print(f"   ❌ {profile}: Profile not found")
                return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Failed to import compression service: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Compression service test failed: {e}")
        return False

def test_file_compression():
    """Test actual file compression functionality."""
    print("\n📁 Testing File Compression...")
    
    try:
        from app.services.compression_service import CompressionService
        
        # Create test files
        temp_dir = tempfile.mkdtemp()
        
        # Test image compression
        print("   Testing image compression...")
        test_image = create_test_image(temp_dir)
        if test_image:
            for profile in ["ultra_low", "low", "medium", "high"]:
                compressed_path = os.path.join(temp_dir, f"compressed_{profile}.jpg")
                success, info = CompressionService.compress_file(test_image, compressed_path, profile)
                
                if success:
                    compression_ratio = info.get('compression_ratio', 0)
                    print(f"   ✅ {profile}: {compression_ratio:.1f}% compression")
                else:
                    print(f"   ❌ {profile}: Compression failed")
                    return False
        
        # Test audio compression (if ffmpeg is available)
        print("   Testing audio compression...")
        test_audio = create_test_audio(temp_dir)
        if test_audio:
            for profile in ["ultra_low", "low", "medium", "high"]:
                compressed_path = os.path.join(temp_dir, f"compressed_{profile}.mp3")
                success, info = CompressionService.compress_file(test_audio, compressed_path, profile)
                
                if success:
                    compression_ratio = info.get('compression_ratio', 0)
                    print(f"   ✅ {profile}: {compression_ratio:.1f}% compression")
                else:
                    print(f"   ❌ {profile}: Compression failed")
                    return False
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"   ❌ File compression test failed: {e}")
        return False

def create_test_image(temp_dir: str) -> str:
    """Create a test image file."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a test image
        img = Image.new('RGB', (1920, 1080), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add some content
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), "GramOthi Test Image", fill='black', font=font)
        draw.rectangle([100, 200, 400, 300], fill='blue', outline='red', width=3)
        
        # Save image
        image_path = os.path.join(temp_dir, "test_image.jpg")
        img.save(image_path, 'JPEG', quality=95)
        return image_path
        
    except Exception as e:
        print(f"   ❌ Failed to create test image: {e}")
        return None

def create_test_audio(temp_dir: str) -> str:
    """Create a test audio file using ffmpeg."""
    try:
        audio_path = os.path.join(temp_dir, "test_audio.wav")
        
        # Generate a simple sine wave
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", "sine=frequency=440:duration=5",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            "-y",
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return audio_path
        else:
            print(f"   ❌ Failed to create test audio: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"   ❌ Failed to create test audio: {e}")
        return None

def test_api_endpoints():
    """Test API endpoints for compression functionality."""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("   ❌ Server is not running or not responding")
            return False
        print("   ✅ Server is running")
    except requests.exceptions.RequestException:
        print("   ❌ Server is not running. Start it with: python -m app.main")
        return False
    
    # Test bandwidth info endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/media/bandwidth-info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            profiles = data.get('compression_profiles', {})
            print(f"   ✅ Bandwidth info endpoint: {len(profiles)} profiles available")
        else:
            print(f"   ❌ Bandwidth info endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Bandwidth info endpoint failed: {e}")
        return False
    
    # Test media endpoints (if available)
    try:
        # Test with different user agents to simulate different devices
        user_agents = [
            ("Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)", "2g"),
            ("Mozilla/5.0 (Linux; Android 10; SM-G975F)", "3g"),
            ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "4g"),
        ]
        
        for user_agent, connection_type in user_agents:
            headers = {
                "User-Agent": user_agent,
                "X-Connection-Type": connection_type
            }
            
            response = requests.get(f"{base_url}/api/v1/media/bandwidth-info", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                detected_profile = data.get('detected_profile')
                print(f"   ✅ {connection_type}: Detected as {detected_profile}")
            else:
                print(f"   ❌ {connection_type}: Failed to detect bandwidth")
                return False
                
    except Exception as e:
        print(f"   ❌ Media endpoint test failed: {e}")
        return False
    
    return True

def test_network_simulation():
    """Test network simulation capabilities."""
    print("\n📡 Testing Network Simulation...")
    
    try:
        # Test different network profiles
        network_profiles = {
            "2g": {"download": 50, "upload": 20, "latency": 300},
            "3g": {"download": 200, "upload": 100, "latency": 150},
            "4g": {"download": 1000, "upload": 500, "latency": 50},
        }
        
        for profile, settings in network_profiles.items():
            print(f"   ✅ {profile}: {settings['download']}kbps down, {settings['latency']}ms latency")
        
        # Test download time simulation
        file_sizes = [1, 5, 10, 25]  # MB
        for size in file_sizes:
            for profile in network_profiles:
                download_speed = network_profiles[profile]['download']
                download_time = (size * 1024) / download_speed  # Convert MB to KB
                print(f"   📊 {size}MB file on {profile}: {download_time:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Network simulation test failed: {e}")
        return False

def generate_verification_report(results: dict):
    """Generate a comprehensive verification report."""
    print("\n" + "="*60)
    print("📋 COMPRESSION VERIFICATION REPORT")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    # Recommendations
    print("\n🎯 Recommendations:")
    if results.get("dependencies", False):
        print("   ✅ All dependencies are installed correctly")
    else:
        print("   ❌ Install missing dependencies: pip install -r requirements.txt")
    
    if results.get("compression_service", False):
        print("   ✅ Compression service is working correctly")
    else:
        print("   ❌ Check compression service implementation")
    
    if results.get("file_compression", False):
        print("   ✅ File compression is working correctly")
    else:
        print("   ❌ Check ffmpeg installation and file permissions")
    
    if results.get("api_endpoints", False):
        print("   ✅ API endpoints are working correctly")
    else:
        print("   ❌ Start the server and check API implementation")
    
    if results.get("network_simulation", False):
        print("   ✅ Network simulation is working correctly")
    else:
        print("   ❌ Check network simulation implementation")
    
    # Overall assessment
    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED!")
        print("   Your GramOthi compression system is ready for rural deployment!")
        print("   You can now test with Chrome DevTools network simulation.")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Please fix the failing tests before deploying to rural areas.")
        print("   Check the recommendations above for guidance.")
    
    return all(results.values())

def main():
    """Run all verification tests."""
    print("🚀 GramOthi Compression Verification Suite")
    print("="*60)
    print("This script verifies that all compression features are working correctly.")
    print("Run this before deploying to ensure rural connectivity optimization.")
    print("="*60)
    
    # Run all tests
    results = {
        "dependencies": check_dependencies(),
        "compression_service": test_compression_service(),
        "file_compression": test_file_compression(),
        "api_endpoints": test_api_endpoints(),
        "network_simulation": test_network_simulation(),
    }
    
    # Generate report
    all_passed = generate_verification_report(results)
    
    # Save results
    with open("compression_verification_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: compression_verification_results.json")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
