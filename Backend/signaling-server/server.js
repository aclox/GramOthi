/**
 * WebRTC Signaling Server for GramOthi
 * Handles WebRTC peer connections, slide synchronization, and real-time communication
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const axios = require('axios');
require('dotenv').config();

const app = express();
const server = http.createServer(app);

// CORS configuration
const io = socketIo(server, {
  cors: {
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ["http://localhost:3000", "http://localhost:8080"],
    methods: ["GET", "POST"],
    credentials: true
  }
});

// Middleware
app.use(cors());
app.use(express.json());

// Store active sessions and connections
const activeSessions = new Map(); // sessionId -> session data
const userConnections = new Map(); // userId -> socket
const classRooms = new Map(); // classId -> Set of user IDs

// Configuration
const CONFIG = {
  FASTAPI_BASE_URL: process.env.FASTAPI_BASE_URL || 'http://localhost:8000',
  TURN_SERVERS: [
    {
      urls: 'turn:localhost:3478',
      username: process.env.TURN_USERNAME || 'gramothi',
      credential: process.env.TURN_PASSWORD || 'gramothi123'
    }
  ],
  ICE_SERVERS: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
};

// Adaptive streaming profiles for poor networks
const ADAPTIVE_PROFILES = {
  emergency: {
    audio: { bitrate: '8k', sampleRate: 16000, channels: 1, codec: 'opus' },
    video: { bitrate: '25k', fps: 3, resolution: '240x180', codec: 'h264' },
    network: { bufferSize: 512, chunkSize: 256, retryAttempts: 5, timeout: 30000 }
  },
  critical: {
    audio: { bitrate: '16k', sampleRate: 22050, channels: 1, codec: 'opus' },
    video: { bitrate: '50k', fps: 5, resolution: '320x240', codec: 'h264' },
    network: { bufferSize: 1024, chunkSize: 512, retryAttempts: 3, timeout: 20000 }
  },
  poor: {
    audio: { bitrate: '32k', sampleRate: 44100, channels: 1, codec: 'opus' },
    video: { bitrate: '100k', fps: 10, resolution: '480x360', codec: 'h264' },
    network: { bufferSize: 2048, chunkSize: 1024, retryAttempts: 2, timeout: 15000 }
  },
  fair: {
    audio: { bitrate: '64k', sampleRate: 44100, channels: 2, codec: 'opus' },
    video: { bitrate: '200k', fps: 15, resolution: '640x480', codec: 'h264' },
    network: { bufferSize: 4096, chunkSize: 2048, retryAttempts: 2, timeout: 10000 }
  },
  good: {
    audio: { bitrate: '128k', sampleRate: 44100, channels: 2, codec: 'opus' },
    video: { bitrate: '400k', fps: 24, resolution: '854x480', codec: 'h264' },
    network: { bufferSize: 8192, chunkSize: 4096, retryAttempts: 1, timeout: 8000 }
  },
  excellent: {
    audio: { bitrate: '192k', sampleRate: 48000, channels: 2, codec: 'opus' },
    video: { bitrate: '800k', fps: 30, resolution: '1280x720', codec: 'h264' },
    network: { bufferSize: 16384, chunkSize: 8192, retryAttempts: 1, timeout: 5000 }
  }
};

/**
 * Get adaptive configuration based on network quality
 */
function getAdaptiveConfig(bandwidth, qualityMetrics, contentType) {
  let profile = 'fair'; // Default profile
  
  // Determine profile based on bandwidth and quality metrics
  if (qualityMetrics) {
    const { latency, packetLoss, jitter } = qualityMetrics;
    
    if (latency > 1000 || packetLoss > 10) {
      profile = 'emergency';
    } else if (latency > 500 || packetLoss > 5) {
      profile = 'critical';
    } else if (latency > 200 || packetLoss > 2) {
      profile = 'poor';
    } else if (latency < 50 && packetLoss < 0.5 && jitter < 10) {
      profile = 'excellent';
    } else if (latency < 100 && packetLoss < 1) {
      profile = 'good';
    }
  } else if (bandwidth) {
    // Fallback to bandwidth-based selection
    switch (bandwidth) {
      case 'ultra_low': profile = 'emergency'; break;
      case 'very_low': profile = 'critical'; break;
      case 'low': profile = 'poor'; break;
      case 'medium': profile = 'fair'; break;
      case 'high': profile = 'good'; break;
      case 'ultra_high': profile = 'excellent'; break;
    }
  }
  
  const config = ADAPTIVE_PROFILES[profile];
  
  return {
    profile: profile,
    contentType: contentType,
    audio: config.audio,
    video: config.video,
    network: config.network,
    optimization: {
      adaptiveBitrate: true,
      errorRecovery: true,
      bufferingStrategy: profile.includes('emergency') || profile.includes('critical') ? 'aggressive' : 'balanced',
      fallbackEnabled: true
    }
  };
}

// Add TURN servers to ICE servers if configured
if (process.env.TURN_SERVERS) {
  CONFIG.ICE_SERVERS.push(...JSON.parse(process.env.TURN_SERVERS));
}

/**
 * Validate user token with FastAPI backend
 */
async function validateToken(token) {
  try {
    const response = await axios.get(`${CONFIG.FASTAPI_BASE_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  } catch (error) {
    console.error('Token validation failed:', error.message);
    return null;
  }
}

/**
 * Get class information from FastAPI backend
 */
async function getClassInfo(classId) {
  try {
    const response = await axios.get(`${CONFIG.FASTAPI_BASE_URL}/api/v1/classes/${classId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to get class info:', error.message);
    return null;
  }
}

/**
 * Create a new live session
 */
async function createLiveSession(classId, teacherId) {
  try {
    const response = await axios.post(`${CONFIG.FASTAPI_BASE_URL}/api/v1/live/sessions`, {
      class_id: classId
    }, {
      headers: { Authorization: `Bearer ${teacherId}` }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to create live session:', error.message);
    return null;
  }
}

/**
 * Handle slide synchronization events
 */
function handleSlideSync(socket, data) {
  const { classId, slideEvent, slideData } = data;
  
  // Broadcast slide event to all users in the class
  const roomUsers = classRooms.get(classId);
  if (roomUsers) {
    roomUsers.forEach(userId => {
      const userSocket = userConnections.get(userId);
      if (userSocket && userSocket.id !== socket.id) {
        userSocket.emit('slide-sync', {
          event: slideEvent, // 'next', 'previous', 'goto'
          slideData: slideData,
          timestamp: Date.now()
        });
      }
    });
  }
}

/**
 * Handle WebRTC signaling
 */
function handleWebRTCSignaling(socket, data) {
  const { targetUserId, signal, type } = data;
  const targetSocket = userConnections.get(targetUserId);
  
  if (targetSocket) {
    targetSocket.emit('webrtc-signal', {
      fromUserId: socket.userId,
      signal: signal,
      type: type
    });
  }
}

/**
 * Handle audio stream control
 */
function handleAudioControl(socket, data) {
  const { classId, action, audioData } = data;
  
  // Broadcast audio control to all users in the class
  const roomUsers = classRooms.get(classId);
  if (roomUsers) {
    roomUsers.forEach(userId => {
      const userSocket = userConnections.get(userId);
      if (userSocket && userSocket.id !== socket.id) {
        userSocket.emit('audio-control', {
          action: action, // 'start', 'stop', 'mute', 'unmute'
          audioData: audioData,
          timestamp: Date.now()
        });
      }
    });
  }
}

// Socket.IO connection handling
io.on('connection', async (socket) => {
  console.log('New connection:', socket.id);
  
  // Handle user authentication
  socket.on('authenticate', async (data) => {
    const { token, classId } = data;
    
    // Validate token
    const user = await validateToken(token);
    if (!user) {
      socket.emit('auth-error', { message: 'Invalid token' });
      return;
    }
    
    // Get class information
    const classInfo = await getClassInfo(classId);
    if (!classInfo) {
      socket.emit('auth-error', { message: 'Class not found' });
      return;
    }
    
    // Store user connection
    socket.userId = user.id;
    socket.classId = classId;
    socket.userRole = user.role;
    userConnections.set(user.id, socket);
    
    // Join class room
    if (!classRooms.has(classId)) {
      classRooms.set(classId, new Set());
    }
    classRooms.get(classId).add(user.id);
    
    // Join socket room
    socket.join(`class-${classId}`);
    
    // Notify other users in the class
    socket.to(`class-${classId}`).emit('user-joined', {
      userId: user.id,
      userName: user.name,
      userRole: user.role
    });
    
    // Send connection success
    socket.emit('authenticated', {
      userId: user.id,
      userName: user.name,
      userRole: user.role,
      classId: classId,
      iceServers: CONFIG.ICE_SERVERS
    });
    
    console.log(`User ${user.name} (${user.role}) joined class ${classId}`);
  });
  
  // Handle slide synchronization
  socket.on('slide-sync', (data) => {
    handleSlideSync(socket, data);
  });
  
  // Handle WebRTC signaling
  socket.on('webrtc-signal', (data) => {
    handleWebRTCSignaling(socket, data);
  });
  
  // Handle audio stream control
  socket.on('audio-control', (data) => {
    handleAudioControl(socket, data);
  });
  
  // Handle chat messages
  socket.on('chat-message', (data) => {
    const { classId, message } = data;
    socket.to(`class-${classId}`).emit('chat-message', {
      userId: socket.userId,
      userName: socket.userName,
      message: message,
      timestamp: Date.now()
    });
  });
  
  // Handle polls and interactions
  socket.on('poll-response', (data) => {
    const { classId, pollId, response } = data;
    socket.to(`class-${classId}`).emit('poll-response', {
      userId: socket.userId,
      pollId: pollId,
      response: response,
      timestamp: Date.now()
    });
  });
  
  // Handle bandwidth detection and network quality
  socket.on('bandwidth-report', (data) => {
    const { classId, bandwidth, connectionType, qualityMetrics } = data;
    // Store bandwidth info for optimization
    socket.bandwidth = bandwidth;
    socket.connectionType = connectionType;
    socket.qualityMetrics = qualityMetrics;
    
    // Notify teacher about student's bandwidth
    const roomUsers = classRooms.get(classId);
    if (roomUsers) {
      roomUsers.forEach(userId => {
        const userSocket = userConnections.get(userId);
        if (userSocket && userSocket.userRole === 'teacher') {
          userSocket.emit('student-bandwidth', {
            userId: socket.userId,
            bandwidth: bandwidth,
            connectionType: connectionType,
            qualityMetrics: qualityMetrics
          });
        }
      });
    }
  });

  // Handle network quality adaptation
  socket.on('quality-adaptation', (data) => {
    const { classId, oldProfile, newProfile, reason } = data;
    
    // Broadcast quality adaptation to all users in the class
    const roomUsers = classRooms.get(classId);
    if (roomUsers) {
      roomUsers.forEach(userId => {
        const userSocket = userConnections.get(userId);
        if (userSocket) {
          userSocket.emit('quality-adaptation', {
            userId: socket.userId,
            oldProfile: oldProfile,
            newProfile: newProfile,
            reason: reason,
            timestamp: Date.now()
          });
        }
      });
    }
  });

  // Handle adaptive streaming requests
  socket.on('request-adaptive-config', (data) => {
    const { classId, contentType } = data;
    
    // Get adaptive configuration based on user's network quality
    const adaptiveConfig = getAdaptiveConfig(socket.bandwidth, socket.qualityMetrics, contentType);
    
    socket.emit('adaptive-config', {
      config: adaptiveConfig,
      timestamp: Date.now()
    });
  });
  
  // Handle disconnection
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
    
    if (socket.userId && socket.classId) {
      // Remove from class room
      const roomUsers = classRooms.get(socket.classId);
      if (roomUsers) {
        roomUsers.delete(socket.userId);
        if (roomUsers.size === 0) {
          classRooms.delete(socket.classId);
        }
      }
      
      // Remove user connection
      userConnections.delete(socket.userId);
      
      // Notify other users
      socket.to(`class-${socket.classId}`).emit('user-left', {
        userId: socket.userId
      });
    }
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'GramOthi Signaling Server',
    version: '1.0.0',
    activeConnections: userConnections.size,
    activeClasses: classRooms.size
  });
});

// Get server configuration
app.get('/config', (req, res) => {
  res.json({
    iceServers: CONFIG.ICE_SERVERS,
    turnServers: CONFIG.TURN_SERVERS
  });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`🚀 GramOthi Signaling Server running on port ${PORT}`);
  console.log(`📡 WebRTC signaling ready for live streaming`);
  console.log(`🎯 TURN servers configured: ${CONFIG.TURN_SERVERS.length > 0 ? 'Yes' : 'No'}`);
});
