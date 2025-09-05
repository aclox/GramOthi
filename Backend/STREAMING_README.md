# 🎥 GramOthi WebRTC Streaming Module

A comprehensive WebRTC-based live streaming solution for the GramOthi educational platform, designed specifically for low-bandwidth rural areas.

## 🚀 Features

### Core Functionality
- **Audio-First Live Streaming**: Optimized for low-bandwidth connections using WebRTC with Opus codec
- **Slide Synchronization**: Real-time slide control with JSON-based events (next/previous/goto)
- **Bandwidth Adaptation**: Automatic quality adjustment based on connection speed
- **Multi-User Support**: Handle multiple students in a single live session
- **Real-time Communication**: WebSocket-based signaling and chat

### Technical Components
- **WebRTC**: Peer-to-peer audio streaming with low latency
- **Node.js Signaling Server**: Handles WebRTC signaling and real-time communication
- **FastAPI Integration**: Seamless integration with existing backend
- **TURN Server**: Coturn-based TURN server for NAT traversal
- **Slide Sync**: JSON-based slide synchronization events

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Signaling      │    │   FastAPI       │
│   (WebRTC)      │◄──►│  Server         │◄──►│   Backend       │
│                 │    │  (Node.js)      │    │   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebRTC        │    │   WebSocket     │    │   Database      │
│   Audio Stream  │    │   Signaling     │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   TURN Server   │
│   (Coturn)      │
└─────────────────┘
```

## 📦 Installation

### Prerequisites
- Node.js 16+
- Python 3.8+
- PostgreSQL 12+
- Docker (for TURN server)

### Quick Setup
```bash
# Run the setup script
chmod +x setup_streaming.sh
./setup_streaming.sh
```

### Manual Setup

1. **Install Python Dependencies**
```bash
pip3 install -r requirements.txt
```

2. **Setup Signaling Server**
```bash
cd signaling-server
npm install
cp env.example .env
# Edit .env with your configuration
```

3. **Setup TURN Server**
```bash
docker-compose -f docker-compose.turn.yml up -d
```

4. **Run Database Migrations**
```bash
alembic upgrade head
```

## 🚀 Usage

### Start All Services
```bash
./start_all.sh
```

### Start Individual Services
```bash
# FastAPI Backend
./start_backend.sh

# Signaling Server
./start_signaling.sh
```

### API Endpoints

#### Streaming Management
- `POST /api/v1/streaming/start` - Start live stream
- `POST /api/v1/streaming/stop` - Stop live stream
- `POST /api/v1/streaming/join` - Join live stream
- `POST /api/v1/streaming/leave` - Leave live stream

#### Slide Synchronization
- `POST /api/v1/streaming/sync-slide` - Sync slide changes
- `GET /api/v1/streaming/slides/{class_id}` - Get class slides

#### Bandwidth Management
- `POST /api/v1/streaming/bandwidth-profile` - Update bandwidth profile
- `GET /api/v1/streaming/status/{class_id}` - Get stream status

#### WebRTC Configuration
- `GET /api/v1/streaming/ice-servers` - Get ICE servers
- `WebSocket /api/v1/streaming/ws/{class_id}` - Real-time communication

## 🔧 Configuration

### Signaling Server (.env)
```env
PORT=3001
FASTAPI_BASE_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
TURN_USERNAME=gramothi
TURN_PASSWORD=gramothi123
```

### TURN Server
```yaml
# docker-compose.turn.yml
services:
  coturn:
    image: coturn/coturn:latest
    ports:
      - "3478:3478"
      - "3478:3478/udp"
    environment:
      - TURN_USERNAME=gramothi
      - TURN_PASSWORD=gramothi123
```

## 📡 WebRTC Implementation

### Audio Streaming
- **Codec**: Opus (optimized for low bandwidth)
- **Bitrate**: Adaptive (32k-192k based on connection)
- **Sample Rate**: 22kHz-44kHz
- **Latency**: < 100ms

### Slide Synchronization
```javascript
// Slide sync events
{
  "type": "slide-sync",
  "data": {
    "action": "next", // "next", "previous", "goto"
    "slide_id": 123,
    "slide_data": {
      "file_url": "/uploads/slide1.pdf",
      "order_no": 1
    },
    "timestamp": 1640995200000
  }
}
```

### Bandwidth Profiles
- **Ultra Low**: < 64kbps (32k audio, 800x600 images)
- **Low**: 64-128kbps (64k audio, 1024x768 images)
- **Medium**: 128-256kbps (128k audio, 1280x720 images)
- **High**: > 256kbps (192k audio, 1920x1080 images)

## 🔌 Integration

### Frontend Integration
```javascript
// Connect to signaling server
const socket = io('http://localhost:3001');

// Authenticate
socket.emit('authenticate', {
  token: 'your-jwt-token',
  classId: 123
});

// Handle slide sync
socket.on('slide-sync', (data) => {
  // Update slide display
  updateSlide(data.slideData);
});

// Send slide control
socket.emit('slide-sync', {
  classId: 123,
  slideEvent: 'next',
  slideData: { slideId: 456 }
});
```

### WebRTC Setup
```javascript
// Create peer connection
const peerConnection = new RTCPeerConnection({
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'turn:localhost:3478', username: 'gramothi', credential: 'gramothi123' }
  ]
});

// Handle audio stream
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    stream.getAudioTracks().forEach(track => {
      peerConnection.addTrack(track, stream);
    });
  });
```

## 🧪 Testing

### Test WebRTC Connection
```bash
# Test signaling server
curl http://localhost:3001/health

# Test FastAPI backend
curl http://localhost:8000/health

# Test ICE servers
curl http://localhost:3001/config
```

### Test Slide Sync
```bash
# Start a live stream
curl -X POST http://localhost:8000/api/v1/streaming/start \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"class_id": 123}'

# Sync a slide
curl -X POST http://localhost:8000/api/v1/streaming/sync-slide \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"class_id": 123, "slide_id": 456, "action": "next"}'
```

## 🐛 Troubleshooting

### Common Issues

1. **WebRTC Connection Failed**
   - Check TURN server is running
   - Verify ICE servers configuration
   - Check firewall settings

2. **Audio Not Working**
   - Verify microphone permissions
   - Check audio codec support
   - Test with different browsers

3. **Slide Sync Issues**
   - Check WebSocket connection
   - Verify authentication token
   - Check class permissions

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=debug
./start_all.sh
```

## 📚 Learning Resources

- [WebRTC Crash Course - Fireship](https://www.youtube.com/watch?v=DvlyzDZDEq4)
- [mediasoup SFU Documentation](https://mediasoup.org/documentation/)
- [TURN Setup: Coturn Guide](https://github.com/coturn/coturn)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the learning resources

---

**Happy Streaming! 🎥✨**
