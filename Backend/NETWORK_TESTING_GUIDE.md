# Network Testing Guide for GramOthi

This guide explains how to test the low-bandwidth optimizations using Chrome DevTools and other network simulation tools.

## 🎯 Testing Objectives

Verify that GramOthi works effectively on:
- **2G Networks** (< 64kbps) - Ultra-low bandwidth
- **3G Networks** (64-128kbps) - Low bandwidth  
- **4G Networks** (128-256kbps) - Medium bandwidth
- **WiFi** (> 256kbps) - High bandwidth

## 🔧 Chrome DevTools Network Simulation

### Step 1: Open Chrome DevTools
1. Open your browser and navigate to your GramOthi frontend
2. Press `F12` or right-click → "Inspect"
3. Go to the **Network** tab

### Step 2: Enable Network Throttling
1. In the Network tab, find the throttling dropdown (usually shows "No throttling")
2. Select one of these presets:
   - **Slow 3G**: 500ms latency, 500kbps down, 500kbps up
   - **Fast 3G**: 150ms latency, 1.6Mbps down, 750kbps up
   - **Custom**: Create your own profile

### Step 3: Create Custom Network Profiles
For more realistic testing, create custom profiles:

#### Ultra-Low Bandwidth (2G Simulation)
- **Download**: 50 kbps
- **Upload**: 20 kbps  
- **Latency**: 300ms
- **Packet Loss**: 0%

#### Low Bandwidth (3G Simulation)
- **Download**: 200 kbps
- **Upload**: 100 kbps
- **Latency**: 150ms
- **Packet Loss**: 0%

#### Medium Bandwidth (4G Simulation)
- **Download**: 1 Mbps
- **Upload**: 500 kbps
- **Latency**: 50ms
- **Packet Loss**: 0%

### Step 4: Test Audio-First Streaming
1. **Start a live session** in your app
2. **Monitor network activity** in DevTools
3. **Verify audio loads first** and plays smoothly
4. **Check compression ratios** in the Network tab
5. **Measure load times** for different file types

### Step 5: Test File Downloads
1. **Upload test files** (audio, images, PDFs)
2. **Download the same files** with different network profiles
3. **Compare file sizes** before and after compression
4. **Measure download times** and user experience

## 📊 What to Look For

### ✅ Success Indicators
- **Audio plays within 2-3 seconds** on 3G
- **Images load progressively** (progressive JPEG)
- **File sizes reduced by 60-80%** after compression
- **No timeouts or failed requests**
- **Smooth user experience** even on slow networks

### ❌ Failure Indicators
- **Audio takes >10 seconds** to start on 3G
- **Images fail to load** or appear broken
- **Large file downloads timeout**
- **Poor user experience** on slow networks
- **No compression applied** to files

## 🧪 Automated Testing

### Run Compression Tests
```bash
cd Backend
python test_compression.py
```

This will test:
- Audio compression across all bandwidth profiles
- Image compression with different quality settings
- Bandwidth detection logic
- API endpoint functionality

### Test Results Interpretation
The test script provides:
- **Compression ratios** for each file type
- **Download time savings** on different networks
- **Bandwidth detection accuracy**
- **Overall system performance**

## 🌐 Real Network Testing

### Mobile Device Testing
1. **Use mobile hotspot** with limited bandwidth
2. **Test on actual 3G/4G networks**
3. **Use network monitoring apps** to measure real performance
4. **Test on different devices** (entry-level smartphones)

### Network Monitoring Tools
- **Chrome DevTools**: Built-in network simulation
- **Firefox DevTools**: Similar network throttling
- **Charles Proxy**: Advanced network simulation
- **Fiddler**: HTTP debugging and simulation

## 📱 Mobile-Specific Testing

### Android Testing
```bash
# Enable mobile data throttling
adb shell settings put global mobile_data 0
adb shell settings put global wifi_sleep_policy 2
```

### iOS Testing
- Use **Network Link Conditioner** (requires Xcode)
- Test on **actual cellular networks**
- Use **Safari Web Inspector** for mobile debugging

## 🔍 Performance Metrics

### Key Metrics to Track
1. **Time to First Audio** (TFA): < 3 seconds on 3G
2. **Time to First Image** (TFI): < 5 seconds on 3G
3. **Compression Ratio**: > 60% for images, > 40% for audio
4. **Download Speed**: Match or exceed network capacity
5. **User Experience**: Smooth playback, no buffering

### Monitoring Tools
- **Chrome DevTools Performance Tab**
- **Network Tab Waterfall View**
- **Lighthouse Performance Audit**
- **WebPageTest.org** for detailed analysis

## 🚀 Production Testing

### Load Testing
```bash
# Test with multiple concurrent users
ab -n 100 -c 10 http://localhost:8000/api/v1/media/bandwidth-info
```

### Stress Testing
- **Simulate 100+ concurrent users**
- **Test with various file sizes**
- **Monitor server performance**
- **Check memory and CPU usage**

## 📋 Testing Checklist

### Pre-Test Setup
- [ ] Chrome DevTools open
- [ ] Network throttling enabled
- [ ] Test files uploaded
- [ ] User accounts created
- [ ] Live session ready

### Audio Testing
- [ ] Audio starts within 3 seconds on 3G
- [ ] No audio dropouts or stuttering
- [ ] Compression reduces file size by >40%
- [ ] Audio quality acceptable for education

### Image Testing
- [ ] Images load progressively
- [ ] Compression reduces file size by >60%
- [ ] Images remain readable and clear
- [ ] No broken or corrupted images

### Overall Experience
- [ ] App remains responsive on slow networks
- [ ] No timeouts or error messages
- [ ] User can complete typical tasks
- [ ] Performance meets rural connectivity needs

## 🎉 Success Criteria

Your GramOthi implementation is ready for rural deployment when:

1. **Audio-first approach works** - Clear voice communication on 3G
2. **Compression is effective** - 60-80% file size reduction
3. **Progressive loading works** - Images and content load gradually
4. **No timeouts occur** - All requests complete successfully
5. **User experience is smooth** - No frustration on slow networks

## 🔧 Troubleshooting

### Common Issues
- **FFmpeg not found**: Install ffmpeg on your system
- **Compression fails**: Check file permissions and disk space
- **Network simulation not working**: Clear browser cache and restart
- **Audio not playing**: Check audio codec support and file format

### Debug Commands
```bash
# Check ffmpeg installation
ffmpeg -version

# Test compression manually
python -c "from app.services.compression_service import CompressionService; print('Compression service loaded')"

# Check network connectivity
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"
```

This comprehensive testing approach ensures that GramOthi delivers excellent performance even in the most challenging network conditions found in rural areas.
