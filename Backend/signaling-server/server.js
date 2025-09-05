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
  
  // Handle bandwidth detection
  socket.on('bandwidth-report', (data) => {
    const { classId, bandwidth, connectionType } = data;
    // Store bandwidth info for optimization
    socket.bandwidth = bandwidth;
    socket.connectionType = connectionType;
    
    // Notify teacher about student's bandwidth
    const roomUsers = classRooms.get(classId);
    if (roomUsers) {
      roomUsers.forEach(userId => {
        const userSocket = userConnections.get(userId);
        if (userSocket && userSocket.userRole === 'teacher') {
          userSocket.emit('student-bandwidth', {
            userId: socket.userId,
            bandwidth: bandwidth,
            connectionType: connectionType
          });
        }
      });
    }
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
