# Teacher Dashboard - Backend Integration Guide

## Database Schema (SQL)

```sql
-- Teacher Dashboard Database Schema
-- Compatible with MySQL, PostgreSQL, SQLite

-- Users/Teachers table
CREATE TABLE teachers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    designation VARCHAR(255) NOT NULL,
    join_date DATE NOT NULL,
    subjects TEXT, -- JSON array or comma-separated
    qualification VARCHAR(255),
    avatar_initials VARCHAR(10),
    theme VARCHAR(20) DEFAULT 'light',
    accent_color VARCHAR(7) DEFAULT '#2563eb',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Students table
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    grade VARCHAR(10),
    last_quiz_score DECIMAL(5,2),
    overall_progress DECIMAL(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

-- Classes table
CREATE TABLE classes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

-- Quizzes table
CREATE TABLE quizzes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('draft', 'active', 'completed', 'archived') DEFAULT 'draft',
    duration_minutes INT DEFAULT 30,
    total_questions INT DEFAULT 0,
    total_attempts INT DEFAULT 0,
    average_score DECIMAL(5,2) DEFAULT 0,
    pending_submissions INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

-- Quiz Questions table
CREATE TABLE quiz_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    quiz_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('multiple_choice', 'true_false', 'short_answer', 'essay') DEFAULT 'multiple_choice',
    points INT DEFAULT 1,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Quiz Options table (for multiple choice questions)
CREATE TABLE quiz_options (
    id INT PRIMARY KEY AUTO_INCREMENT,
    question_id INT NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
);

-- Student Quiz Attempts table
CREATE TABLE student_quiz_attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    quiz_id INT NOT NULL,
    score DECIMAL(5,2),
    total_questions INT,
    correct_answers INT,
    time_taken_minutes INT,
    status ENUM('in_progress', 'completed', 'abandoned') DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Student Quiz Answers table
CREATE TABLE student_quiz_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    attempt_id INT NOT NULL,
    question_id INT NOT NULL,
    answer_text TEXT,
    selected_option_id INT,
    is_correct BOOLEAN,
    points_earned DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES student_quiz_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES quiz_options(id) ON DELETE SET NULL
);

-- Uploaded Files table
CREATE TABLE uploaded_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    category ENUM('material', 'notes', 'presentation') DEFAULT 'material',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

-- Notes table
CREATE TABLE notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    file_id INT,
    note_type ENUM('text', 'file', 'url') DEFAULT 'text',
    tags TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES uploaded_files(id) ON DELETE SET NULL
);

-- Live Sessions table
CREATE TABLE live_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('scheduled', 'live', 'ended', 'cancelled') DEFAULT 'scheduled',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INT DEFAULT 0,
    participant_count INT DEFAULT 0,
    recording_url VARCHAR(500),
    is_recording BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

-- Recordings table
CREATE TABLE recordings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    session_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    file_size BIGINT,
    duration_minutes INT,
    thumbnail_url VARCHAR(500),
    is_public BOOLEAN DEFAULT FALSE,
    view_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE SET NULL
);

-- Student Progress table
CREATE TABLE student_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    teacher_id INT NOT NULL,
    quiz_completion_rate DECIMAL(5,2) DEFAULT 0,
    average_quiz_score DECIMAL(5,2) DEFAULT 0,
    total_quizzes_attempted INT DEFAULT 0,
    total_quizzes_completed INT DEFAULT 0,
    last_activity_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_progress (student_id, teacher_id)
);

-- Notifications table
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('info', 'success', 'warning', 'error') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX idx_teachers_email ON teachers(email);
CREATE INDEX idx_students_teacher_id ON students(teacher_id);
CREATE INDEX idx_quizzes_teacher_id ON quizzes(teacher_id);
CREATE INDEX idx_quiz_questions_quiz_id ON quiz_questions(quiz_id);
CREATE INDEX idx_student_quiz_attempts_student_id ON student_quiz_attempts(student_id);
CREATE INDEX idx_student_quiz_attempts_quiz_id ON student_quiz_attempts(quiz_id);
CREATE INDEX idx_uploaded_files_teacher_id ON uploaded_files(teacher_id);
CREATE INDEX idx_notes_teacher_id ON notes(teacher_id);
CREATE INDEX idx_live_sessions_teacher_id ON live_sessions(teacher_id);
CREATE INDEX idx_recordings_teacher_id ON recordings(teacher_id);
CREATE INDEX idx_notifications_teacher_id ON notifications(teacher_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
```

## Sample Data

```sql
-- Insert sample teacher
INSERT INTO teachers (email, password_hash, name, designation, join_date, subjects, qualification, avatar_initials, theme, accent_color) 
VALUES ('sarah.johnson@university.edu', '$2b$10$example_hash', 'Dr. Sarah Johnson', 'Senior Mathematics Professor', '2020-01-15', 'Math, Statistics', 'PhD Mathematics', 'SJ', 'light', '#2563eb');

-- Insert sample students
INSERT INTO students (teacher_id, name, email, grade, last_quiz_score, overall_progress) VALUES
(1, 'Alex Johnson', 'alex.johnson@student.edu', 'A+', 95.00, 92.00),
(1, 'Sarah Miller', 'sarah.miller@student.edu', 'A', 88.00, 88.00),
(1, 'Mike Davis', 'mike.davis@student.edu', 'B+', 82.00, 78.00);

-- Insert sample classes
INSERT INTO classes (teacher_id, name, description, subject) VALUES
(1, 'Calculus I', 'Introduction to differential calculus', 'Mathematics'),
(1, 'Statistics 101', 'Basic statistical concepts and methods', 'Statistics'),
(1, 'Advanced Mathematics', 'Advanced mathematical concepts', 'Mathematics');

-- Insert sample quizzes
INSERT INTO quizzes (teacher_id, title, description, status, duration_minutes, total_questions, total_attempts, average_score, pending_submissions) VALUES
(1, 'Algebra Basics - Chapter 1', 'Basic algebraic concepts and operations', 'active', 30, 15, 24, 87.50, 3),
(1, 'Statistics Fundamentals', 'Introduction to statistical methods', 'draft', 45, 20, 0, 0.00, 0);

-- Insert sample uploaded files
INSERT INTO uploaded_files (teacher_id, file_name, original_name, file_type, file_size, file_path, category) VALUES
(1, 'calc_chapter3_notes.pdf', 'Calculus Chapter 3 Notes.pdf', 'application/pdf', 2457600, '/uploads/calc_chapter3_notes.pdf', 'notes'),
(1, 'stats_formulas.doc', 'Statistics Formulas.doc', 'application/msword', 1152000, '/uploads/stats_formulas.doc', 'notes');

-- Insert sample notes
INSERT INTO notes (teacher_id, title, content, file_id, note_type, tags) VALUES
(1, 'Calculus Chapter 3 Notes', 'Important concepts from chapter 3', 1, 'file', '["calculus", "chapter3", "notes"]'),
(1, 'Statistics Formulas', 'Common statistical formulas and equations', 2, 'file', '["statistics", "formulas", "reference"]');

-- Insert sample live session
INSERT INTO live_sessions (teacher_id, title, description, status, start_time, is_recording) VALUES
(1, 'Live Calculus Session', 'Interactive calculus problem solving', 'live', NOW(), TRUE);

-- Insert sample recording
INSERT INTO recordings (teacher_id, session_id, title, description, file_path, duration_minutes) VALUES
(1, 1, 'Lecture • 2024-01-15 10:30:00', 'Recorded calculus session', '/recordings/lecture_20240115_103000.mp4', 45);
```

## API Endpoints Documentation

### Authentication
```
POST /api/auth/login
POST /api/auth/register
POST /api/auth/logout
GET /api/auth/profile
PUT /api/auth/profile
```

### Teacher Profile
```
GET /api/teachers/profile
PUT /api/teachers/profile
GET /api/teachers/dashboard-stats
```

### Students Management
```
GET /api/students
POST /api/students
GET /api/students/:id
PUT /api/students/:id
DELETE /api/students/:id
GET /api/students/:id/progress
```

### Quizzes Management
```
GET /api/quizzes
POST /api/quizzes
GET /api/quizzes/:id
PUT /api/quizzes/:id
DELETE /api/quizzes/:id
POST /api/quizzes/:id/questions
PUT /api/quizzes/:id/questions/:questionId
DELETE /api/quizzes/:id/questions/:questionId
GET /api/quizzes/:id/attempts
POST /api/quizzes/:id/attempts
```

### Files & Notes
```
GET /api/files
POST /api/files/upload
GET /api/files/:id
DELETE /api/files/:id
GET /api/notes
POST /api/notes
PUT /api/notes/:id
DELETE /api/notes/:id
```

### Live Sessions & Recordings
```
GET /api/sessions
POST /api/sessions
PUT /api/sessions/:id
DELETE /api/sessions/:id
POST /api/sessions/:id/start-recording
POST /api/sessions/:id/stop-recording
GET /api/recordings
POST /api/recordings
DELETE /api/recordings/:id
```

## API Request/Response Examples

### 1. Teacher Profile Update
```javascript
// PUT /api/teachers/profile
{
  "name": "Dr. Sarah Johnson",
  "designation": "Senior Mathematics Professor",
  "join_date": "2020-01-15",
  "subjects": "Math, Statistics",
  "qualification": "PhD Mathematics",
  "theme": "light",
  "accent_color": "#2563eb"
}

// Response
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Dr. Sarah Johnson",
    "designation": "Senior Mathematics Professor",
    "join_date": "2020-01-15",
    "subjects": "Math, Statistics",
    "qualification": "PhD Mathematics",
    "avatar_initials": "SJ",
    "theme": "light",
    "accent_color": "#2563eb",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2. Dashboard Statistics
```javascript
// GET /api/teachers/dashboard-stats
// Response
{
  "success": true,
  "data": {
    "total_classes": 3,
    "total_students": 24,
    "uploaded_files": 5,
    "recorded_sessions": 8,
    "active_quizzes": 2,
    "pending_quizzes": 1,
    "recent_uploads": [
      {
        "id": 1,
        "name": "Calculus Chapter 3 Notes.pdf",
        "size": 2457600,
        "type": "application/pdf",
        "created_at": "2024-01-15T09:00:00Z"
      }
    ],
    "recent_recordings": [
      {
        "id": 1,
        "title": "Lecture • 2024-01-15 10:30:00",
        "duration_minutes": 45,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

### 3. Students List
```javascript
// GET /api/students
// Response
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Alex Johnson",
      "email": "alex.johnson@student.edu",
      "grade": "A+",
      "last_quiz_score": 95.00,
      "overall_progress": 92.00,
      "created_at": "2024-01-10T08:00:00Z"
    },
    {
      "id": 2,
      "name": "Sarah Miller",
      "email": "sarah.miller@student.edu",
      "grade": "A",
      "last_quiz_score": 88.00,
      "overall_progress": 88.00,
      "created_at": "2024-01-10T08:00:00Z"
    }
  ]
}
```

### 4. Quiz Creation
```javascript
// POST /api/quizzes
{
  "title": "Algebra Basics - Chapter 1",
  "description": "Basic algebraic concepts and operations",
  "duration_minutes": 30,
  "questions": [
    {
      "question_text": "What is 2x + 3x?",
      "question_type": "multiple_choice",
      "points": 1,
      "options": [
        { "option_text": "5x", "is_correct": true },
        { "option_text": "6x", "is_correct": false },
        { "option_text": "5", "is_correct": false },
        { "option_text": "6", "is_correct": false }
      ]
    }
  ]
}

// Response
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Algebra Basics - Chapter 1",
    "description": "Basic algebraic concepts and operations",
    "status": "draft",
    "duration_minutes": 30,
    "total_questions": 1,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 5. File Upload
```javascript
// POST /api/files/upload
// FormData with file
{
  "file": File,
  "category": "notes"
}

// Response
{
  "success": true,
  "data": {
    "id": 1,
    "file_name": "calc_chapter3_notes.pdf",
    "original_name": "Calculus Chapter 3 Notes.pdf",
    "file_type": "application/pdf",
    "file_size": 2457600,
    "file_path": "/uploads/calc_chapter3_notes.pdf",
    "category": "notes",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Frontend Integration Code

### JavaScript API Client
```javascript
// api-client.js
class TeacherDashboardAPI {
  constructor(baseURL = 'http://localhost:3000/api') {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('auth_token');
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

  // Teacher Profile
  async getProfile() {
    return this.request('/teachers/profile');
  }

  async updateProfile(profileData) {
    return this.request('/teachers/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  async getDashboardStats() {
    return this.request('/teachers/dashboard-stats');
  }

  // Students
  async getStudents() {
    return this.request('/students');
  }

  async createStudent(studentData) {
    return this.request('/students', {
      method: 'POST',
      body: JSON.stringify(studentData)
    });
  }

  async updateStudent(id, studentData) {
    return this.request(`/students/${id}`, {
      method: 'PUT',
      body: JSON.stringify(studentData)
    });
  }

  async deleteStudent(id) {
    return this.request(`/students/${id}`, {
      method: 'DELETE'
    });
  }

  // Quizzes
  async getQuizzes() {
    return this.request('/quizzes');
  }

  async createQuiz(quizData) {
    return this.request('/quizzes', {
      method: 'POST',
      body: JSON.stringify(quizData)
    });
  }

  async updateQuiz(id, quizData) {
    return this.request(`/quizzes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(quizData)
    });
  }

  async deleteQuiz(id) {
    return this.request(`/quizzes/${id}`, {
      method: 'DELETE'
    });
  }

  // Files
  async getFiles() {
    return this.request('/files');
  }

  async uploadFile(file, category = 'material') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    return this.request('/files/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
  }

  async deleteFile(id) {
    return this.request(`/files/${id}`, {
      method: 'DELETE'
    });
  }

  // Notes
  async getNotes() {
    return this.request('/notes');
  }

  async createNote(noteData) {
    return this.request('/notes', {
      method: 'POST',
      body: JSON.stringify(noteData)
    });
  }

  async updateNote(id, noteData) {
    return this.request(`/notes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(noteData)
    });
  }

  async deleteNote(id) {
    return this.request(`/notes/${id}`, {
      method: 'DELETE'
    });
  }

  // Live Sessions
  async getSessions() {
    return this.request('/sessions');
  }

  async createSession(sessionData) {
    return this.request('/sessions', {
      method: 'POST',
      body: JSON.stringify(sessionData)
    });
  }

  async startRecording(sessionId) {
    return this.request(`/sessions/${sessionId}/start-recording`, {
      method: 'POST'
    });
  }

  async stopRecording(sessionId) {
    return this.request(`/sessions/${sessionId}/stop-recording`, {
      method: 'POST'
    });
  }

  // Recordings
  async getRecordings() {
    return this.request('/recordings');
  }

  async deleteRecording(id) {
    return this.request(`/recordings/${id}`, {
      method: 'DELETE'
    });
  }
}

// Initialize API client
const api = new TeacherDashboardAPI();
```

### Updated Frontend Code Integration
```javascript
// Update your existing app.js to use the API
async function loadProfile() {
  try {
    const response = await api.getProfile();
    state.profile = response.data;
    updateProfileDisplay();
  } catch (error) {
    console.error('Failed to load profile:', error);
  }
}

async function saveProfile() {
  try {
    const profileData = {
      name: $('#editName').value.trim(),
      designation: $('#editDesignation').value.trim(),
      join_date: $('#editJoinDate').value.trim(),
      subjects: $('#editSubjects').value.trim(),
      qualification: $('#editQualification').value.trim()
    };
    
    const response = await api.updateProfile(profileData);
    state.profile = response.data;
    updateProfileDisplay();
    cancelProfileEdit();
  } catch (error) {
    console.error('Failed to save profile:', error);
    alert('Failed to save profile. Please try again.');
  }
}

async function loadDashboardStats() {
  try {
    const response = await api.getDashboardStats();
    const stats = response.data;
    
    $('#statClasses').textContent = stats.total_classes;
    $('#statFiles').textContent = stats.uploaded_files;
    $('#statRecordings').textContent = stats.recorded_sessions;
    $('#statStudents').textContent = stats.total_students;
    $('#statQuizzes').textContent = stats.active_quizzes;
  } catch (error) {
    console.error('Failed to load dashboard stats:', error);
  }
}

async function loadStudents() {
  try {
    const response = await api.getStudents();
    state.students = response.data;
    renderStudentsList();
  } catch (error) {
    console.error('Failed to load students:', error);
  }
}

async function loadQuizzes() {
  try {
    const response = await api.getQuizzes();
    state.quizzes = response.data;
    renderQuizzesList();
  } catch (error) {
    console.error('Failed to load quizzes:', error);
  }
}

async function loadFiles() {
  try {
    const response = await api.getFiles();
    state.uploadedFiles = response.data;
    renderFilesList();
  } catch (error) {
    console.error('Failed to load files:', error);
  }
}

async function loadNotes() {
  try {
    const response = await api.getNotes();
    state.notes = response.data;
    renderNotesList();
  } catch (error) {
    console.error('Failed to load notes:', error);
  }
}

async function loadRecordings() {
  try {
    const response = await api.getRecordings();
    state.recordings = response.data;
    renderRecordingsList();
  } catch (error) {
    console.error('Failed to load recordings:', error);
  }
}
```

## Environment Configuration

### .env file
```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=teacher_dashboard
DB_USER=your_username
DB_PASSWORD=your_password

# JWT Secret
JWT_SECRET=your_jwt_secret_key

# File Upload
UPLOAD_PATH=/uploads
MAX_FILE_SIZE=10485760

# Server
PORT=3000
NODE_ENV=development
```

## Backend Framework Examples

### Node.js/Express
```javascript
// server.js
const express = require('express');
const mysql = require('mysql2');
const multer = require('multer');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 3000;

// Database connection
const db = mysql.createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME
});

// Middleware
app.use(express.json());
app.use(express.static('public'));

// File upload configuration
const upload = multer({
  dest: process.env.UPLOAD_PATH,
  limits: { fileSize: parseInt(process.env.MAX_FILE_SIZE) }
});

// Routes
app.get('/api/teachers/profile', authenticateToken, (req, res) => {
  // Implementation
});

app.put('/api/teachers/profile', authenticateToken, (req, res) => {
  // Implementation
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Python/Django
```python
# models.py
from django.db import models

class Teacher(models.Model):
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    join_date = models.DateField()
    subjects = models.TextField()
    qualification = models.CharField(max_length=255)
    avatar_initials = models.CharField(max_length=10)
    theme = models.CharField(max_length=20, default='light')
    accent_color = models.CharField(max_length=7, default='#2563eb')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        # Implementation
        pass
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        # Implementation
        pass
```

This comprehensive guide provides everything you need to integrate the teacher dashboard with a backend system, including database schema, API documentation, sample data, and frontend integration code.
