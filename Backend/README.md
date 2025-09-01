# GramOthi - Low-Bandwidth Virtual Classroom Backend

A robust backend infrastructure designed specifically for low-bandwidth rural areas, enabling virtual classrooms with minimal data requirements.

## 🎯 Project Overview

GramOthi addresses the critical challenge of providing quality education in rural areas with limited internet connectivity. The platform prioritizes:

- **Audio Quality**: Crystal clear voice communication even on low bandwidth
- **Compressed Visual Content**: Optimized slides and materials for slow connections
- **Offline Access**: Downloadable content for offline learning
- **Interactive Elements**: Quizzes, polls, and discussions that work on entry-level smartphones
- **Simple Interface**: Minimal learning curve for both educators and students

## 🏗️ Architecture

### Core Components
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database for data persistence
- **SQLAlchemy**: Python SQL toolkit and ORM
- **Alembic**: Database migration management
- **JWT**: Secure authentication system
- **WebSockets**: Real-time communication for live sessions

### Database Models
- **Users**: Students and teachers with role-based access
- **Classes**: Virtual classroom sessions
- **Slides**: Educational materials (PDFs, presentations, images)
- **Recordings**: Audio recordings with optional bundled content
- **Quizzes**: Interactive assessments
- **Live Sessions**: Real-time classroom sessions
- **Polls**: Quick feedback and engagement tools
- **Discussions**: Asynchronous communication threads

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GramOthi/Backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials and other settings
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb gramothi
   
   # Run initial migration
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   python -m app.main
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/refresh` - Refresh access token

### Class Management
- `POST /api/v1/classes/` - Create new class
- `GET /api/v1/classes/` - List user's classes
- `GET /api/v1/classes/{class_id}` - Get class details
- `PUT /api/v1/classes/{class_id}` - Update class
- `DELETE /api/v1/classes/{class_id}` - Delete class

### Content Management
- `POST /api/v1/classes/{class_id}/slides` - Upload slides
- `GET /api/v1/classes/{class_id}/slides` - Get class slides
- `POST /api/v1/classes/{class_id}/recordings` - Upload recordings
- `GET /api/v1/classes/{class_id}/recordings` - Get class recordings

### Interactive Features
- `POST /api/v1/quizzes/` - Create quiz
- `POST /api/v1/quizzes/{quiz_id}/respond` - Submit quiz response
- `POST /api/v1/live/polls/` - Create poll
- `POST /api/v1/live/polls/{poll_id}/vote` - Vote on poll
- `POST /api/v1/live/discussions/` - Create discussion post

### Live Sessions
- `POST /api/v1/live/sessions` - Start live session
- `PUT /api/v1/live/sessions/{session_id}/end` - End live session
- `GET /api/v1/live/sessions/class/{class_id}` - Get active session
- `WS /api/v1/live/ws/{class_id}` - WebSocket for real-time communication

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key for authentication
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration time
- `MAX_FILE_SIZE`: Maximum file upload size in bytes
- `UPLOAD_DIR`: Directory for storing uploaded files

### Database Configuration
The application uses PostgreSQL with the following default settings:
- Database: `gramothi`
- Port: `5432`
- Encoding: `UTF-8`

## 📁 Project Structure

```
Backend/
├── alembic/                 # Database migrations
│   ├── env.py              # Migration environment
│   └── script.py.mako      # Migration template
├── app/
│   ├── routes/             # API route handlers
│   │   ├── auth.py         # Authentication routes
│   │   ├── class.py        # Class management routes
│   │   ├── quiz.py         # Quiz routes
│   │   └── live.py         # Live session routes
│   ├── services/           # Business logic
│   │   └── auth_service.py # Authentication service
│   ├── config.py           # Database configuration
│   ├── database.py         # Database connection
│   ├── main.py             # FastAPI application
│   ├── models.py           # Database models
│   └── schemas.py          # Pydantic schemas
├── uploads/                 # File storage directory
├── requirements.txt         # Python dependencies
├── alembic.ini             # Alembic configuration
├── env.example             # Environment variables template
└── README.md               # This file
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Test Coverage
```bash
pip install pytest-cov
pytest --cov=app tests/
```

## 🚀 Deployment

### Production Considerations
1. **Environment Variables**: Use strong, unique secrets
2. **Database**: Use connection pooling and SSL
3. **File Storage**: Consider cloud storage (AWS S3, Google Cloud Storage)
4. **Caching**: Implement Redis for session management
5. **Load Balancing**: Use Nginx or similar for production
6. **Monitoring**: Implement logging and health checks

### Docker Deployment
```bash
# Build image
docker build -t gramothi-backend .

# Run container
docker run -p 8000:8000 --env-file .env gramothi-backend
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Different permissions for students and teachers
- **Input Validation**: Comprehensive request validation using Pydantic
- **File Upload Security**: File type and size validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## 📊 Performance Optimizations

- **Low-Bandwidth Design**: Optimized for rural internet connections
- **File Compression**: Automatic compression of uploaded content
- **Caching**: Redis-based caching for frequently accessed data
- **Database Indexing**: Optimized database queries
- **Async Operations**: Non-blocking I/O operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is part of the Smart India Hackathon and is designed for educational purposes.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/docs` when the server is running

## 🎉 Acknowledgments

- Smart India Hackathon organizers
- Rural education advocates
- Open source community contributors
