/**
 * GramOthi Teacher Dashboard App
 * Main application logic for the teacher dashboard
 */

// Global state
let teacherState = {
    user: null,
    classes: [],
    students: [],
    quizzes: [],
    currentTab: 'dashboard',
    profileModal: null
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('GramOthi Teacher Dashboard initialized');
    
    // Check authentication
    checkAuthentication();
    
    // Initialize profile modal
    teacherState.profileModal = document.getElementById('profileModal');
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize UI
    initializeUI();
    
    // Load teacher data
    loadTeacherData();
});

function checkAuthentication() {
    const user = localStorage.getItem('gramothi_user');
    if (!user) {
        window.location.href = 'auth.html';
        return;
    }
    
    try {
        teacherState.user = JSON.parse(user);
        if (teacherState.user.role !== 'teacher') {
            window.location.href = 'index.html';
            return;
        }
    } catch (error) {
        console.error('Error parsing user data:', error);
        window.location.href = 'auth.html';
    }
}

function setupEventListeners() {
    // Tab navigation
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
    
    // Profile avatar click
    const profileAvatar = document.querySelector('.header-avatar');
    if (profileAvatar) {
        profileAvatar.addEventListener('click', function() {
            openProfileModal();
        });
    }
    
    // Profile modal close
    const profileModal = document.getElementById('profileModal');
    if (profileModal) {
        profileModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeProfileModal();
            }
        });
    }
    
    // Save profile button
    const saveProfileBtn = document.getElementById('saveProfile');
    if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', function() {
            saveProfile();
        });
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            logout();
        });
    }
    
    // Create class buttons
    const createClassBtns = document.querySelectorAll('#createClassBtn, #createClassBtn2');
    createClassBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            createClass();
        });
    });
    
    // Add student button
    const addStudentBtn = document.getElementById('addStudentBtn');
    if (addStudentBtn) {
        addStudentBtn.addEventListener('click', function() {
            addStudent();
        });
    }
    
    // Create quiz button
    const createQuizBtn = document.getElementById('createQuizBtn');
    if (createQuizBtn) {
        createQuizBtn.addEventListener('click', function() {
            createQuiz();
        });
    }
    
    // Live session buttons
    const startLiveBtns = document.querySelectorAll('#startLiveBtn, #startLiveSessionBtn');
    startLiveBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            startLiveSession();
        });
    });
    
    const startRecordingBtn = document.getElementById('startRecordingBtn');
    if (startRecordingBtn) {
        startRecordingBtn.addEventListener('click', function() {
            startRecording();
        });
    }
    
    // File upload
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function() {
            handleFileUpload(this.files);
        });
    }
    
    // Search functionality
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            performSearch();
        });
    }
    
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        globalSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

function initializeUI() {
    // Set up live clock
    updateClock();
    setInterval(updateClock, 1000);
    
    // Load dashboard data
    loadDashboardData();
}

function updateClock() {
    const clockElement = document.getElementById('liveClock');
    if (clockElement) {
        const now = new Date();
        clockElement.textContent = now.toLocaleTimeString();
    }
}

function switchTab(tabName) {
    // Update tab buttons
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });
    
    // Update panels
    const panels = document.querySelectorAll('.panel');
    panels.forEach(panel => {
        panel.classList.remove('active');
        if (panel.id === `tab-${tabName}`) {
            panel.classList.add('active');
        }
    });
    
    teacherState.currentTab = tabName;
    
    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch (tabName) {
        case 'classes':
            loadClasses();
            break;
        case 'students':
            loadStudents();
            break;
        case 'quizzes':
            loadQuizzes();
            break;
        case 'files':
            loadFiles();
            break;
        case 'analytics':
            loadAnalytics();
            break;
    }
}

function openProfileModal() {
    if (teacherState.profileModal) {
        teacherState.profileModal.showModal();
        loadProfileData();
    }
}

function closeProfileModal() {
    if (teacherState.profileModal) {
        teacherState.profileModal.close();
    }
}

function loadProfileData() {
    // Load teacher profile data into form
    const profileName = document.getElementById('profileName');
    const profileEmail = document.getElementById('profileEmail');
    const profileSubject = document.getElementById('profileSubject');
    const profileExperience = document.getElementById('profileExperience');
    const profilePhone = document.getElementById('profilePhone');
    
    if (teacherState.user) {
        if (profileName) profileName.value = teacherState.user.name || '';
        if (profileEmail) profileEmail.value = teacherState.user.email || '';
        if (profileSubject) profileSubject.value = teacherState.user.subject || '';
        if (profileExperience) profileExperience.value = teacherState.user.experience || '';
        if (profilePhone) profilePhone.value = teacherState.user.phone || '';
    }
}

function saveProfile() {
    // Get form data
    const profileData = {
        name: document.getElementById('profileName')?.value || '',
        email: document.getElementById('profileEmail')?.value || '',
        subject: document.getElementById('profileSubject')?.value || '',
        experience: document.getElementById('profileExperience')?.value || '',
        phone: document.getElementById('profilePhone')?.value || ''
    };
    
    // Validate required fields
    if (!profileData.name || !profileData.email) {
        alert('Please enter your name and email');
        return;
    }
    
    // Save profile data
    try {
        // Update state
        teacherState.user = { ...teacherState.user, ...profileData };
        
        // Save to localStorage
        localStorage.setItem('gramothi_user', JSON.stringify(teacherState.user));
        
        // Show success message
        alert('Profile saved successfully!');
        
        // Close modal
        closeProfileModal();
        
        // Update UI
        updateUserDisplay();
        
    } catch (error) {
        console.error('Error saving profile:', error);
        alert('Error saving profile. Please try again.');
    }
}

function loadTeacherData() {
    // Load teacher data from localStorage
    const savedUser = localStorage.getItem('gramothi_user');
    if (savedUser) {
        try {
            teacherState.user = JSON.parse(savedUser);
            updateUserDisplay();
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }
}

function updateUserDisplay() {
    // Update header with user info
    const headerAvatar = document.querySelector('.header-avatar');
    if (headerAvatar && teacherState.user) {
        headerAvatar.title = teacherState.user.name || 'Teacher Profile';
    }
}

function loadDashboardData() {
    // Load dashboard statistics
    updateDashboardStats();
    loadRecentActivity();
}

function updateDashboardStats() {
    // Update statistics cards
    const totalClasses = document.getElementById('totalClasses');
    const totalStudents = document.getElementById('totalStudents');
    const totalQuizzes = document.getElementById('totalQuizzes');
    const liveSessions = document.getElementById('liveSessions');
    
    if (totalClasses) totalClasses.textContent = teacherState.classes.length;
    if (totalStudents) totalStudents.textContent = teacherState.students.length;
    if (totalQuizzes) totalQuizzes.textContent = teacherState.quizzes.length;
    if (liveSessions) liveSessions.textContent = '0'; // Placeholder
}

function loadRecentActivity() {
    const recentActivity = document.getElementById('recentActivity');
    if (recentActivity) {
        const activities = [
            'Created new class "Mathematics 101"',
            'Added 5 new students',
            'Published quiz "Algebra Basics"',
            'Started live session for Class A'
        ];
        
        recentActivity.innerHTML = activities.map(activity => `<li>${activity}</li>`).join('');
    }
}

function createClass() {
    const className = prompt('Enter class name:');
    if (!className) return;
    
    const classDescription = prompt('Enter class description (optional):') || '';
    
    const newClass = {
        id: Date.now(),
        name: className,
        description: classDescription,
        createdAt: new Date().toISOString(),
        studentCount: 0
    };
    
    teacherState.classes.push(newClass);
    updateDashboardStats();
    
    if (teacherState.currentTab === 'classes') {
        loadClasses();
    }
    
    alert(`Class "${className}" created successfully!`);
}

function loadClasses() {
    const classesList = document.getElementById('classesList');
    if (!classesList) return;
    
    if (teacherState.classes.length === 0) {
        classesList.innerHTML = '<div class="empty-state"><p>No classes created yet. Create your first class to get started!</p></div>';
        return;
    }
    
    classesList.innerHTML = teacherState.classes.map(cls => `
        <div class="card">
            <h3>${cls.name}</h3>
            <p>${cls.description}</p>
            <div class="card-actions">
                <button class="btn btn-sm">Manage</button>
                <button class="btn-outline btn-sm">View Students</button>
            </div>
        </div>
    `).join('');
}

function addStudent() {
    const studentName = prompt('Enter student name:');
    if (!studentName) return;
    
    const studentEmail = prompt('Enter student email:');
    if (!studentEmail) return;
    
    const newStudent = {
        id: Date.now(),
        name: studentName,
        email: studentEmail,
        grade: '10th',
        progress: 0,
        addedAt: new Date().toISOString()
    };
    
    teacherState.students.push(newStudent);
    updateDashboardStats();
    
    if (teacherState.currentTab === 'students') {
        loadStudents();
    }
    
    alert(`Student "${studentName}" added successfully!`);
}

function loadStudents() {
    const studentsList = document.getElementById('studentsList');
    if (!studentsList) return;
    
    if (teacherState.students.length === 0) {
        studentsList.innerHTML = '<div class="empty-state"><p>No students added yet. Add your first student to get started!</p></div>';
        return;
    }
    
    studentsList.innerHTML = teacherState.students.map(student => `
        <div class="card">
            <h3>${student.name}</h3>
            <p>${student.email}</p>
            <p>Grade: ${student.grade}</p>
            <div class="card-actions">
                <button class="btn btn-sm">View Progress</button>
                <button class="btn-outline btn-sm">Edit</button>
            </div>
        </div>
    `).join('');
}

function createQuiz() {
    const quizTitle = prompt('Enter quiz title:');
    if (!quizTitle) return;
    
    const quizDescription = prompt('Enter quiz description (optional):') || '';
    
    const newQuiz = {
        id: Date.now(),
        title: quizTitle,
        description: quizDescription,
        questions: [],
        createdAt: new Date().toISOString(),
        status: 'draft'
    };
    
    teacherState.quizzes.push(newQuiz);
    updateDashboardStats();
    
    if (teacherState.currentTab === 'quizzes') {
        loadQuizzes();
    }
    
    alert(`Quiz "${quizTitle}" created successfully!`);
}

function loadQuizzes() {
    const quizzesList = document.getElementById('quizzesList');
    if (!quizzesList) return;
    
    if (teacherState.quizzes.length === 0) {
        quizzesList.innerHTML = '<div class="empty-state"><p>No quizzes created yet. Create your first quiz to get started!</p></div>';
        return;
    }
    
    quizzesList.innerHTML = teacherState.quizzes.map(quiz => `
        <div class="card">
            <h3>${quiz.title}</h3>
            <p>${quiz.description}</p>
            <p>Status: ${quiz.status}</p>
            <div class="card-actions">
                <button class="btn btn-sm">Edit</button>
                <button class="btn-outline btn-sm">Publish</button>
            </div>
        </div>
    `).join('');
}

function loadFiles() {
    const filesList = document.getElementById('filesList');
    if (!filesList) return;
    
    filesList.innerHTML = '<div class="empty-state"><p>No files uploaded yet. Upload your first file to get started!</p></div>';
}

function loadAnalytics() {
    // Placeholder for analytics
    console.log('Loading analytics...');
}

function startLiveSession() {
    alert('Live session functionality would be implemented here with WebRTC');
}

function startRecording() {
    alert('Recording functionality would be implemented here');
}

function handleFileUpload(files) {
    if (files.length === 0) return;
    
    alert(`Uploading ${files.length} file(s)...`);
    // File upload logic would be implemented here
}

function performSearch() {
    const searchTerm = document.getElementById('globalSearch')?.value;
    if (!searchTerm) {
        alert('Please enter a search term');
        return;
    }
    
    console.log('Searching for:', searchTerm);
    alert(`Searching for: ${searchTerm}`);
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Clear user data
        localStorage.removeItem('gramothi_user');
        localStorage.removeItem('gramothi_auth_token');
        teacherState.user = null;
        
        // Redirect to auth page
        window.location.href = 'auth.html';
    }
}

// Export functions for global access
window.GramOthiTeacherApp = {
    openProfileModal,
    closeProfileModal,
    saveProfile,
    switchTab,
    createClass,
    addStudent,
    createQuiz,
    startLiveSession,
    performSearch,
    logout
};
