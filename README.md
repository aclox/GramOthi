# GramOthi

A comprehensive educational platform with live streaming, progress tracking, and interactive learning features.

## 🚀 Project Overview

GramOthi is a full-stack educational application that provides:
- **Live Streaming**: Real-time video streaming for educational content
- **Progress Tracking**: Comprehensive student progress monitoring
- **Quiz System**: Interactive assessments and evaluations
- **Media Management**: Efficient handling of educational content
- **Notification System**: Real-time updates and alerts
- **Data Synchronization**: Seamless data sync across devices

## 🏗️ Architecture

The project follows a modern microservices architecture with:
- **Backend**: FastAPI-based Python backend with PostgreSQL database
- **Database**: PostgreSQL with Alembic migrations
- **Authentication**: JWT-based authentication system
- **File Handling**: Efficient media compression and storage
- **Real-time**: WebSocket support for live features

## 📁 Project Structure

```
Backend/
├── app/
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   └── main.py          # FastAPI application
├── alembic/              # Database migrations
├── tests/                # Test suite
└── requirements.txt      # Python dependencies
```

## 🛠️ Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Docker (optional)
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/aclox/GramOthi.git
cd GramOthi
```

### 2. Backend Setup
```bash
cd Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your database credentials
```

### 3. Database Setup
```bash
# Start PostgreSQL (using Docker)
docker-compose up -d postgres

# Or use your local PostgreSQL instance
# Update .env with your database connection details

# Run migrations
alembic upgrade head
```

### 4. Start the Application
```bash
# Start the backend server
python -m uvicorn app.main:app --reload

# The API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the Backend directory:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/gramothi
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database Configuration
- **Host**: localhost (or your database host)
- **Port**: 5432 (default PostgreSQL port)
- **Database**: gramothi
- **Username/Password**: Your PostgreSQL credentials

## 📚 API Documentation

Once the server is running, you can access:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🧪 Testing

```bash
cd Backend

# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/test_auth.py

# Run with coverage
python -m pytest --cov=app tests/
```

## 🚀 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Follow the existing code structure
- Add tests for new functionality
- Update documentation as needed

### 3. Commit Your Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

### 4. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## 📝 Code Style

- **Python**: Follow PEP 8 guidelines
- **API**: RESTful design principles
- **Database**: Use Alembic for schema changes
- **Testing**: Maintain good test coverage
- **Documentation**: Keep README and code comments updated

## 🔍 Key Features

### Authentication System
- JWT-based authentication
- User registration and login
- Role-based access control

### Live Streaming
- Real-time video streaming
- WebSocket support
- Session management

### Progress Tracking
- Student progress monitoring
- Achievement tracking
- Performance analytics

### Media Management
- File upload and storage
- Compression optimization
- Content delivery

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Contribution Guidelines
- Follow the existing code style
- Add tests for new features
- Update documentation
- Use meaningful commit messages
- Keep PRs focused and small

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists

**Migration Errors**
- Check Alembic version compatibility
- Verify database schema matches models
- Run `alembic current` to check status

**Import Errors**
- Activate virtual environment
- Install missing dependencies
- Check Python path

## 📞 Support

- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the `/docs` folder for detailed guides

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI community for the excellent web framework
- PostgreSQL team for the robust database
- All contributors who help improve this project

---

**Happy Coding! 🎉**

For more detailed information, check the individual documentation files in the project.
