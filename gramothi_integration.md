# Teacher Dashboard - GramOthi Backend Integration

## Backend Services Overview

Based on the [GramOthi repository](https://github.com/aclox/GramOthi/commit/a6d8ba2318cd9a1cec3aa5d2cb7828cf51d007d3), your backend includes:

- **CompressionService** - Video compression and optimization
- **VideoQualityService** - Quality profile management
- **NetworkQualityService** - Adaptive quality based on network conditions
- **WebRTCService** - Real-time communication
- **Signaling Server** - WebRTC signaling coordination
- **Quality Profiles** - Centralized configuration management

## Updated API Integration

### 1. Enhanced API Client for GramOthi Backend

```javascript
// gramothi-api-client.js
class GramOthiTeacherAPI {
  constructor(baseURL = 'http://localhost:8000/api') {
    this.baseURL = baseURL;
    this.signalingURL = 'ws://localhost:8080';
    this.token = localStorage.getItem('auth_token');
    this.webrtcConnection = null;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
        ...options.headers
      },
      ...options
    };

    const response = await fetch(url, config);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || 'API request failed');
    }
    
    return data;
  }

  // Teacher Profile with Video Quality Settings
  async getProfile() {
    return this.request('/teachers/profile');
  }

  async updateProfile(profileData) {
    return this.request('/teachers/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  // Video Quality Management
  async getQualityProfiles() {
    return this.request('/video/quality-profiles');
  }

  async updateQualityProfile(profileId, settings) {
    return this.request(`/video/quality-profiles/${profileId}`, {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
  }

  // Live Session with WebRTC
  async createLiveSession(sessionData) {
    return this.request('/sessions/live', {
      method: 'POST',
      body: JSON.stringify({
        ...sessionData,
        webrtc_enabled: true,
        quality_profile: 'adaptive'
      })
    });
  }

  async startLiveSession(sessionId) {
    return this.request(`/sessions/${sessionId}/start`, {
      method: 'POST'
    });
  }

  async stopLiveSession(sessionId) {
    return this.request(`/sessions/${sessionId}/stop`, {
      method: 'POST'
    });
  }

  // Recording with Compression
  async startRecording(sessionId, compressionSettings = {}) {
    return this.request(`/sessions/${sessionId}/recording/start`, {
      method: 'POST',
      body: JSON.stringify({
        compression_profile: 'balanced',
        quality: 'high',
        ...compressionSettings
      })
    });
  }

  async stopRecording(sessionId) {
    return this.request(`/sessions/${sessionId}/recording/stop`, {
      method: 'POST'
    });
  }

  async getRecordingStatus(sessionId) {
    return this.request(`/sessions/${sessionId}/recording/status`);
  }

  // Video File Management
  async uploadVideo(file, qualityProfile = 'auto') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('quality_profile', qualityProfile);
    formData.append('auto_compress', 'true');

    return this.request('/videos/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
  }

  async compressVideo(videoId, compressionSettings) {
    return this.request(`/videos/${videoId}/compress`, {
      method: 'POST',
      body: JSON.stringify(compressionSettings)
    });
  }

  async getVideoCompressionStatus(videoId) {
    return this.request(`/videos/${videoId}/compression/status`);
  }

  // Network Quality Monitoring
  async getNetworkQuality() {
    return this.request('/network/quality');
  }

  async updateNetworkSettings(settings) {
    return this.request('/network/settings', {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
  }

  // WebRTC Connection Management
  async initializeWebRTC(sessionId) {
    try {
      this.webrtcConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      });

      // Set up signaling connection
      this.signalingSocket = new WebSocket(`${this.signalingURL}/session/${sessionId}`);
      
      this.signalingSocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleSignalingMessage(message);
      };

      return { success: true, connection: this.webrtcConnection };
    } catch (error) {
      throw new Error(`WebRTC initialization failed: ${error.message}`);
    }
  }

  async handleSignalingMessage(message) {
    switch (message.type) {
      case 'offer':
        await this.handleOffer(message.offer);
        break;
      case 'answer':
        await this.handleAnswer(message.answer);
        break;
      case 'ice-candidate':
        await this.handleIceCandidate(message.candidate);
        break;
    }
  }

  async handleOffer(offer) {
    await this.webrtcConnection.setRemoteDescription(offer);
    const answer = await this.webrtcConnection.createAnswer();
    await this.webrtcConnection.setLocalDescription(answer);
    
    this.signalingSocket.send(JSON.stringify({
      type: 'answer',
      answer: answer
    }));
  }

  async handleAnswer(answer) {
    await this.webrtcConnection.setRemoteDescription(answer);
  }

  async handleIceCandidate(candidate) {
    await this.webrtcConnection.addIceCandidate(candidate);
  }

  // Dashboard Statistics with Video Metrics
  async getDashboardStats() {
    return this.request('/teachers/dashboard-stats');
  }

  // Enhanced Students Management
  async getStudents() {
    return this.request('/students');
  }

  async getStudentVideoProgress(studentId) {
    return this.request(`/students/${studentId}/video-progress`);
  }

  // Quizzes with Video Integration
  async createQuiz(quizData) {
    return this.request('/quizzes', {
      method: 'POST',
      body: JSON.stringify({
        ...quizData,
        video_enabled: true,
        recording_allowed: true
      })
    });
  }

  // File Management with Compression
  async uploadFile(file, category = 'material', autoCompress = true) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    formData.append('auto_compress', autoCompress.toString());

    return this.request('/files/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
  }

  // Notes with Video Attachments
  async createNote(noteData) {
    return this.request('/notes', {
      method: 'POST',
      body: JSON.stringify({
        ...noteData,
        video_attachments: noteData.video_attachments || []
      })
    });
  }

  // Cleanup
  disconnect() {
    if (this.webrtcConnection) {
      this.webrtcConnection.close();
    }
    if (this.signalingSocket) {
      this.signalingSocket.close();
    }
  }
}

// Initialize API client
const gramothiAPI = new GramOthiTeacherAPI();
```

### 2. Enhanced Frontend Integration

```javascript
// gramothi-integration.js
class GramOthiTeacherDashboard {
  constructor() {
    this.api = gramothiAPI;
    this.isLive = false;
    this.isRecording = false;
    this.currentSession = null;
    this.videoElement = null;
    this.stream = null;
  }

  // Initialize WebRTC for live sessions
  async initializeVideo() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        },
        audio: true
      });

      this.videoElement = document.getElementById('liveVideo');
      if (this.videoElement) {
        this.videoElement.srcObject = this.stream;
      }

      return this.stream;
    } catch (error) {
      console.error('Error accessing camera:', error);
      throw error;
    }
  }

  // Enhanced Live Session Management
  async startLiveSession() {
    try {
      // Initialize video
      await this.initializeVideo();

      // Create live session
      const sessionData = {
        title: `Live Session - ${new Date().toLocaleString()}`,
        description: 'Interactive teaching session',
        quality_profile: 'adaptive',
        recording_enabled: true
      };

      const response = await this.api.createLiveSession(sessionData);
      this.currentSession = response.data;

      // Initialize WebRTC
      await this.api.initializeWebRTC(this.currentSession.id);

      // Start session
      await this.api.startLiveSession(this.currentSession.id);

      this.isLive = true;
      this.updateLiveStatus();
      
      return this.currentSession;
    } catch (error) {
      console.error('Failed to start live session:', error);
      throw error;
    }
  }

  async stopLiveSession() {
    try {
      if (this.currentSession) {
        await this.api.stopLiveSession(this.currentSession.id);
        
        // Stop video stream
        if (this.stream) {
          this.stream.getTracks().forEach(track => track.stop());
        }

        // Disconnect WebRTC
        this.api.disconnect();

        this.isLive = false;
        this.currentSession = null;
        this.updateLiveStatus();
      }
    } catch (error) {
      console.error('Failed to stop live session:', error);
      throw error;
    }
  }

  // Enhanced Recording with Compression
  async startRecording() {
    try {
      if (!this.currentSession) {
        throw new Error('No active live session');
      }

      const compressionSettings = {
        quality: 'high',
        bitrate: 'auto',
        resolution: '720p',
        frame_rate: 30
      };

      await this.api.startRecording(this.currentSession.id, compressionSettings);
      this.isRecording = true;
      this.updateRecordingStatus();

      // Monitor compression status
      this.monitorCompressionStatus();
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  }

  async stopRecording() {
    try {
      if (this.currentSession) {
        await this.api.stopRecording(this.currentSession.id);
        this.isRecording = false;
        this.updateRecordingStatus();

        // Add recording to list
        this.addRecordingToList();
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
      throw error;
    }
  }

  // Monitor video compression status
  async monitorCompressionStatus() {
    if (!this.currentSession) return;

    const checkStatus = async () => {
      try {
        const status = await this.api.getRecordingStatus(this.currentSession.id);
        
        if (status.data.compression_status === 'completed') {
          console.log('Video compression completed');
          this.updateRecordingList();
        } else if (status.data.compression_status === 'processing') {
          console.log('Video compression in progress...');
          setTimeout(checkStatus, 5000); // Check again in 5 seconds
        }
      } catch (error) {
        console.error('Error checking compression status:', error);
      }
    };

    setTimeout(checkStatus, 2000); // Start checking after 2 seconds
  }

  // Enhanced File Upload with Video Compression
  async uploadFile(file, category = 'material') {
    try {
      const isVideo = file.type.startsWith('video/');
      const autoCompress = isVideo; // Auto-compress video files

      const response = await this.api.uploadFile(file, category, autoCompress);
      
      if (isVideo) {
        // Monitor compression for video files
        this.monitorVideoCompression(response.data.id);
      }

      return response.data;
    } catch (error) {
      console.error('Failed to upload file:', error);
      throw error;
    }
  }

  async monitorVideoCompression(videoId) {
    const checkCompression = async () => {
      try {
        const status = await this.api.getVideoCompressionStatus(videoId);
        
        if (status.data.status === 'completed') {
          console.log(`Video ${videoId} compression completed`);
          this.updateFilesList();
        } else if (status.data.status === 'processing') {
          console.log(`Video ${videoId} compression in progress...`);
          setTimeout(checkCompression, 3000);
        }
      } catch (error) {
        console.error('Error checking video compression:', error);
      }
    };

    setTimeout(checkCompression, 1000);
  }

  // Network Quality Monitoring
  async updateNetworkQuality() {
    try {
      const quality = await this.api.getNetworkQuality();
      this.displayNetworkQuality(quality.data);
    } catch (error) {
      console.error('Failed to get network quality:', error);
    }
  }

  displayNetworkQuality(quality) {
    const qualityIndicator = document.getElementById('networkQuality');
    if (qualityIndicator) {
      qualityIndicator.textContent = `Network: ${quality.quality} (${quality.bandwidth}Mbps)`;
      qualityIndicator.className = `network-indicator ${quality.quality.toLowerCase()}`;
    }
  }

  // Update UI Status
  updateLiveStatus() {
    const statusElement = document.getElementById('liveStatusChip');
    if (statusElement) {
      statusElement.textContent = `Live: ${this.isLive ? 'Online' : 'Offline'}`;
      statusElement.className = `chip ${this.isLive ? 'live-online' : 'live-offline'}`;
    }
  }

  updateRecordingStatus() {
    const statusElement = document.getElementById('recordQuickToggle');
    if (statusElement) {
      statusElement.textContent = `Recording: ${this.isRecording ? 'On' : 'Off'}`;
      statusElement.className = `btn ${this.isRecording ? 'recording-on' : 'recording-off'}`;
    }
  }

  addRecordingToList() {
    if (this.currentSession) {
      const recording = {
        id: Date.now(),
        title: `Lecture • ${new Date().toLocaleString()}`,
        startedAt: Date.now(),
        sessionId: this.currentSession.id,
        compressed: true
      };

      // Add to state and update UI
      state.recordings.push(recording);
      renderRecordingsList();
      renderDashboard();
    }
  }

  updateRecordingList() {
    // Refresh recordings list to show compressed versions
    renderRecordingsList();
  }

  updateFilesList() {
    // Refresh files list to show compressed videos
    renderFilesList();
  }
}

// Initialize enhanced dashboard
const gramothiDashboard = new GramOthiTeacherDashboard();
```

### 3. Updated HTML with Video Elements

```html
<!-- Add to your existing HTML -->
<!-- Live Video Section -->
<section class="section" id="live-video">
    <div class="card">
        <div class="card-header">Live Video Stream</div>
        <div class="card-body">
            <div class="video-container">
                <video id="liveVideo" autoplay muted playsinline style="width: 100%; max-width: 800px; border-radius: 8px;"></video>
                <div class="video-controls">
                    <button id="startVideoBtn" class="btn btn-primary">Start Camera</button>
                    <button id="stopVideoBtn" class="btn" style="display: none;">Stop Camera</button>
                </div>
            </div>
            <div class="network-status">
                <span id="networkQuality" class="network-indicator">Network: Checking...</span>
            </div>
        </div>
    </div>
</section>

<!-- Enhanced Live Session Controls -->
<section class="section" id="lecture">
    <div class="grid grid-2">
        <div class="card">
            <div class="card-header">Live Session</div>
            <div class="card-body">
                <div class="row" style="align-items:center; justify-content: space-between;">
                    <div>
                        <div style="font-weight:700">Status</div>
                        <div class="muted">Toggle to go Online or Offline</div>
                    </div>
                    <button class="toggle" id="liveToggle" aria-pressed="false" aria-label="Toggle live"></button>
                </div>
                <div class="spacer"></div>
                <div class="video-quality-settings">
                    <label>Video Quality:</label>
                    <select id="qualitySelect" class="select">
                        <option value="auto">Auto (Adaptive)</option>
                        <option value="high">High (1080p)</option>
                        <option value="medium">Medium (720p)</option>
                        <option value="low">Low (480p)</option>
                    </select>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-header">Recording</div>
            <div class="card-body">
                <div class="row" style="align-items:center; justify-content: space-between;">
                    <div>
                        <div style="font-weight:700">Recording Control</div>
                        <div class="muted">Start/Stop recording with compression</div>
                    </div>
                    <button class="btn" id="recordBtn">Start Recording</button>
                </div>
                <div class="spacer"></div>
                <div class="compression-status" id="compressionStatus" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill" id="compressionProgress"></div>
                    </div>
                    <span class="muted">Compressing video...</span>
                </div>
            </div>
        </div>
    </div>
</section>
```

### 4. Enhanced CSS for Video Elements

```css
/* Add to your existing styles.css */

/* Video Container */
.video-container {
    position: relative;
    background: #000;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 16px;
}

.video-controls {
    position: absolute;
    bottom: 16px;
    left: 16px;
    display: flex;
    gap: 8px;
}

/* Network Quality Indicator */
.network-indicator {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}

.network-indicator.excellent {
    background: #10b981;
    color: white;
}

.network-indicator.good {
    background: #3b82f6;
    color: white;
}

.network-indicator.fair {
    background: #f59e0b;
    color: white;
}

.network-indicator.poor {
    background: #ef4444;
    color: white;
}

/* Live Status Indicators */
.chip.live-online {
    background: #10b981;
    color: white;
}

.chip.live-offline {
    background: #6b7280;
    color: white;
}

.btn.recording-on {
    background: #ef4444;
    color: white;
}

.btn.recording-off {
    background: #6b7280;
    color: white;
}

/* Compression Status */
.compression-status {
    margin-top: 12px;
    padding: 12px;
    background: rgba(37, 99, 235, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(37, 99, 235, 0.2);
}

/* Video Quality Settings */
.video-quality-settings {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
}

.video-quality-settings label {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-muted);
}

/* Enhanced Progress Bars */
.progress-bar {
    width: 100%;
    height: 8px;
    border-radius: 4px;
    background: rgba(37, 99, 235, 0.1);
    overflow: hidden;
    position: relative;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-strong));
    transition: width 300ms ease;
    position: relative;
}

.progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}
```

### 5. Integration with Existing Code

```javascript
// Update your existing app.js initialization
function init() {
    // ... existing initialization code ...

    // Enhanced live session controls
    $('#liveToggle').addEventListener('click', async () => {
        if (gramothiDashboard.isLive) {
            await gramothiDashboard.stopLiveSession();
        } else {
            await gramothiDashboard.startLiveSession();
        }
    });

    // Enhanced recording controls
    $('#recordBtn').addEventListener('click', async () => {
        if (gramothiDashboard.isRecording) {
            await gramothiDashboard.stopRecording();
        } else {
            await gramothiDashboard.startRecording();
        }
    });

    // Video quality settings
    $('#qualitySelect').addEventListener('change', async (e) => {
        const quality = e.target.value;
        await gramothiAPI.updateNetworkSettings({ quality_profile: quality });
    });

    // Initialize network quality monitoring
    setInterval(() => {
        gramothiDashboard.updateNetworkQuality();
    }, 10000); // Check every 10 seconds

    // ... rest of existing initialization code ...
}
```

This integration connects your teacher dashboard with the GramOthi backend services, providing:

- **Real-time video streaming** with WebRTC
- **Automatic video compression** using the CompressionService
- **Adaptive quality management** based on network conditions
- **Enhanced recording capabilities** with compression
- **Network quality monitoring** and display
- **Seamless integration** with existing dashboard features

The system now leverages all the backend services from the [GramOthi repository](https://github.com/aclox/GramOthi/commit/a6d8ba2318cd9a1cec3aa5d2cb7828cf51d007d3) while maintaining the clean, modern UI of your teacher dashboard.
