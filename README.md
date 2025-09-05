# Student Dashboard - GramOthi Integration

A modern student dashboard integrated with the [GramOthi eLearning platform](https://github.com/aclox/GramOthi) backend.

## 🚀 Features

- **Authentication**: Integrated with GramOthi FastAPI backend
- **Role-based Access**: Student and Teacher dashboards
- **Real-time Data**: Live classes, quizzes, and progress tracking
- **Offline Support**: PWA with service worker caching
- **Responsive Design**: Clean blue and white theme

## 🏗️ Architecture

### Frontend (This Project)
- **HTML/CSS/JavaScript**: Vanilla JS with modern ES6+
- **PWA**: Service worker for offline functionality
- **IndexedDB**: Local data storage
- **API Integration**: RESTful communication with GramOthi backend

### Backend Integration
- **GramOthi Backend**: FastAPI-based Python backend
- **Authentication**: JWT token-based auth
- **Database**: PostgreSQL with user management
- **Real-time**: WebSocket support for live features

## 📁 Project Structure

```
student dashboard/
├── index.html              # Main dashboard
├── auth.html               # Login/signup page
├── src/
│   ├── api.js             # GramOthi API integration
│   ├── auth.js            # Authentication logic
│   ├── app.js             # Main application logic
│   ├── idb.js             # IndexedDB wrapper
│   └── styles.css         # Styling
├── sw.js                  # Service worker
├── manifest.webmanifest   # PWA manifest
└── icons/                 # PWA icons
```

## 🛠️ Setup

### 1. Clone GramOthi Backend
```bash
git clone https://github.com/aclox/GramOthi.git
cd GramOthi/Backend
```

### 2. Setup GramOthi Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Start backend server
python -m uvicorn app.main:app --reload
```

### 3. Setup Student Dashboard
```bash
# Serve the dashboard (requires local server for PWA)
python -m http.server 5500
# Or use any other local server
```

### 4. Access the Application
- **Dashboard**: http://localhost:5500
- **GramOthi API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔧 Configuration

### API Configuration
Update the API base URL in `src/api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000'; // GramOthi backend URL
```

### Environment Variables (GramOthi Backend)
Create `.env` file in GramOthi Backend directory:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/gramothi
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📚 API Integration

### Authentication Flow
1. User selects role (Student/Teacher)
2. Login attempts GramOthi backend first
3. Falls back to local storage if backend unavailable
4. JWT token stored for authenticated requests

### Data Synchronization
- **Classes**: Real-time class joining/leaving
- **Profile**: User profile updates
- **Quizzes**: Quiz completion tracking
- **Progress**: Learning progress monitoring

### Offline Support
- Service worker caches essential resources
- IndexedDB stores data locally
- Syncs with backend when connection restored

## 🎯 Key Features

### Student Dashboard
- **Profile Management**: Personal information and photo upload
- **Class Management**: Join/leave classes with real-time updates
- **Quiz System**: Interactive quizzes with progress tracking
- **Video Lectures**: Stream educational content
- **Progress Tracking**: Monitor learning achievements

### Teacher Dashboard
- **Class Creation**: Create and manage classes
- **Quiz Management**: Create and monitor quizzes
- **Student Analytics**: Track student progress
- **Content Upload**: Manage educational materials

## 🔍 API Endpoints Used

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user

### Classes
- `GET /classes` - Get user's classes
- `POST /classes/join` - Join a class
- `DELETE /classes/{id}/leave` - Leave a class

### Profile
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update user profile

### Quizzes
- `GET /quizzes` - Get available quizzes
- `POST /quizzes/{id}/submit` - Submit quiz answers

## 🚀 Deployment

### Backend Deployment
Follow GramOthi's deployment instructions for the FastAPI backend.

### Frontend Deployment
1. Update API_BASE_URL to production backend URL
2. Deploy to any static hosting service (Netlify, Vercel, etc.)
3. Ensure HTTPS for PWA functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with GramOthi backend
5. Submit a pull request

## 📄 License

This project integrates with GramOthi and follows the same MIT License.

## 🙏 Acknowledgments

- [GramOthi](https://github.com/aclox/GramOthi) - The comprehensive eLearning platform
- FastAPI community for the excellent backend framework
- All contributors who help improve this integration

---

**Happy Learning! 🎓**

