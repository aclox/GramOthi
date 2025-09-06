/**
 * Unified GramOthi Application
 * Handles both student and teacher dashboards
 */

class UnifiedGramOthiApp {
    constructor() {
        this.currentUser = null;
        this.currentRole = null;
        this.api = new GramOthiAPI();
        this.init();
    }

    async init() {
        console.log('Initializing Unified GramOthi App...');
        
        // Check if user is already authenticated
        const token = localStorage.getItem('auth_token');
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        
        if (token && user) {
            this.currentUser = user;
            this.currentRole = user.role;
            this.showDashboard();
        } else {
            this.showAuth();
        }

        // Initialize event listeners
        this.initEventListeners();
        
        // Initialize clock
        this.initClock();
        
        // Initialize PWA
        this.initPWA();
    }

    initEventListeners() {
        // Authentication form
        const authForm = document.getElementById('authForm');
        if (authForm) {
            authForm.addEventListener('submit', (e) => this.handleAuth(e));
        }

        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Role selection
        const roleStudent = document.getElementById('roleStudent');
        const roleTeacher = document.getElementById('roleTeacher');
        const roleStudentReg = document.getElementById('roleStudentReg');
        const roleTeacherReg = document.getElementById('roleTeacherReg');

        if (roleStudent) roleStudent.addEventListener('click', () => this.selectRole('student'));
        if (roleTeacher) roleTeacher.addEventListener('click', () => this.selectRole('teacher'));
        if (roleStudentReg) roleStudentReg.addEventListener('click', () => this.selectRole('student', 'reg'));
        if (roleTeacherReg) roleTeacherReg.addEventListener('click', () => this.selectRole('teacher', 'reg'));

        // Auth tabs
        const authTabs = document.querySelectorAll('.auth-tab');
        authTabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchAuthTab(tab.dataset.tab));
        });

        // Profile modal
        const profileModal = document.getElementById('profileModal');
        if (profileModal) {
            profileModal.addEventListener('click', (e) => {
                if (e.target === profileModal) {
                    this.closeProfileModal();
                }
            });
        }

        // Logout
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }

        // Save profile
        const saveProfile = document.getElementById('saveProfile');
        if (saveProfile) {
            saveProfile.addEventListener('click', () => this.saveProfile());
        }

        // Navigation tabs
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        // Sidebar
        const sideOpen = document.getElementById('sideOpen');
        const sideClose = document.getElementById('sideClose');
        if (sideOpen) sideOpen.addEventListener('click', () => this.toggleSidebar(true));
        if (sideClose) sideClose.addEventListener('click', () => this.toggleSidebar(false));

        // Search
        const searchBtn = document.getElementById('searchBtn');
        const globalSearch = document.getElementById('globalSearch');
        if (searchBtn) searchBtn.addEventListener('click', () => this.handleSearch());
        if (globalSearch) {
            globalSearch.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.handleSearch();
            });
        }

        // Teacher-specific buttons
        const createClassBtn = document.getElementById('createClassBtn');
        const createClassBtn2 = document.getElementById('createClassBtn2');
        if (createClassBtn) createClassBtn.addEventListener('click', () => this.createClass());
        if (createClassBtn2) createClassBtn2.addEventListener('click', () => this.createClass());

        const startLiveBtn = document.getElementById('startLiveBtn');
        const startLiveSessionBtn = document.getElementById('startLiveSessionBtn');
        if (startLiveBtn) startLiveBtn.addEventListener('click', () => this.startLiveSession());
        if (startLiveSessionBtn) startLiveSessionBtn.addEventListener('click', () => this.startLiveSession());

        // File upload
        const uploadBtn = document.getElementById('uploadBtn');
        const fileInput = document.getElementById('fileInput');
        if (uploadBtn && fileInput) {
            uploadBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }
    }

    showAuth() {
        document.getElementById('authSection').style.display = 'block';
        document.getElementById('studentDashboard').style.display = 'none';
        document.getElementById('teacherDashboard').style.display = 'none';
    }

    showDashboard() {
        document.getElementById('authSection').style.display = 'none';
        
        if (this.currentRole === 'teacher') {
            document.getElementById('studentDashboard').style.display = 'none';
            document.getElementById('teacherDashboard').style.display = 'block';
            this.initTeacherDashboard();
        } else {
            document.getElementById('studentDashboard').style.display = 'block';
            document.getElementById('teacherDashboard').style.display = 'none';
            this.initStudentDashboard();
        }
    }

    async handleAuth(e) {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const response = await this.api.login(email, password);
            this.currentUser = response.user;
            this.currentRole = response.user.role;
            localStorage.setItem('auth_token', response.access_token);
            localStorage.setItem('user', JSON.stringify(response.user));
            this.showDashboard();
        } catch (error) {
            console.error('Login failed:', error);
            alert('Login failed. Please check your credentials.');
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const name = document.getElementById('regName').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;

        try {
            const response = await this.api.register(email, password, this.currentRole, name);
            this.currentUser = response.user;
            this.currentRole = response.user.role;
            localStorage.setItem('auth_token', response.access_token);
            localStorage.setItem('user', JSON.stringify(response.user));
            this.showDashboard();
        } catch (error) {
            console.error('Registration failed:', error);
            alert('Registration failed. Please try again.');
        }
    }

    selectRole(role, form = 'login') {
        this.currentRole = role;
        
        if (form === 'login') {
            const roleStudent = document.getElementById('roleStudent');
            const roleTeacher = document.getElementById('roleTeacher');
            if (roleStudent && roleTeacher) {
                roleStudent.className = role === 'student' ? 'btn' : 'btn-outline';
                roleTeacher.className = role === 'teacher' ? 'btn' : 'btn-outline';
            }
        } else {
            const roleStudentReg = document.getElementById('roleStudentReg');
            const roleTeacherReg = document.getElementById('roleTeacherReg');
            if (roleStudentReg && roleTeacherReg) {
                roleStudentReg.className = role === 'student' ? 'btn' : 'btn-outline';
                roleTeacherReg.className = role === 'teacher' ? 'btn' : 'btn-outline';
            }
        }
    }

    switchAuthTab(tab) {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const loginTab = document.querySelector('[data-tab="login"]');
        const registerTab = document.querySelector('[data-tab="register"]');

        if (tab === 'login') {
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
        } else {
            loginForm.classList.remove('active');
            registerForm.classList.add('active');
            loginTab.classList.remove('active');
            registerTab.classList.add('active');
        }
    }

    switchTab(tabName) {
        // Hide all panels
        const panels = document.querySelectorAll('.panel');
        panels.forEach(panel => panel.classList.remove('active'));

        // Show selected panel
        const selectedPanel = document.getElementById(`tab-${tabName}`);
        if (selectedPanel) {
            selectedPanel.classList.add('active');
        }

        // Update tab buttons
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => tab.classList.remove('active'));
        const selectedTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (selectedTab) {
            selectedTab.classList.add('active');
        }
    }

    toggleSidebar(open) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('open', open);
        }
    }

    handleSearch() {
        const searchTerm = document.getElementById('globalSearch').value;
        console.log('Searching for:', searchTerm);
        // Implement search functionality
    }

    initStudentDashboard() {
        console.log('Initializing student dashboard...');
        this.loadStudentData();
    }

    initTeacherDashboard() {
        console.log('Initializing teacher dashboard...');
        this.loadTeacherData();
    }

    async loadStudentData() {
        try {
            // Load student-specific data
            console.log('Loading student data...');
        } catch (error) {
            console.error('Failed to load student data:', error);
        }
    }

    async loadTeacherData() {
        try {
            // Load teacher-specific data
            console.log('Loading teacher data...');
        } catch (error) {
            console.error('Failed to load teacher data:', error);
        }
    }

    createClass() {
        const className = prompt('Enter class name:');
        if (className) {
            console.log('Creating class:', className);
            // Implement class creation
        }
    }

    startLiveSession() {
        console.log('Starting live session...');
        // Implement live session functionality
    }

    handleFileUpload(e) {
        const files = Array.from(e.target.files);
        console.log('Uploading files:', files);
        // Implement file upload
    }

    initClock() {
        const updateClock = () => {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            const clockElement = document.getElementById('liveClock');
            if (clockElement) {
                clockElement.textContent = timeString;
            }
        };
        
        updateClock();
        setInterval(updateClock, 1000);
    }

    initPWA() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('SW registered: ', registration);
                })
                .catch(registrationError => {
                    console.log('SW registration failed: ', registrationError);
                });
        }

        // Handle install prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const installBtn = document.getElementById('installBtn');
            if (installBtn) {
                installBtn.hidden = false;
                installBtn.addEventListener('click', () => {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('User accepted the install prompt');
                        }
                        deferredPrompt = null;
                    });
                });
            }
        });
    }

    openProfileModal() {
        const modal = document.getElementById('profileModal');
        if (modal) {
            this.populateProfileForm();
            modal.showModal();
        }
    }

    closeProfileModal() {
        const modal = document.getElementById('profileModal');
        if (modal) {
            modal.close();
        }
    }

    populateProfileForm() {
        if (this.currentUser) {
            document.getElementById('profileName').value = this.currentUser.name || '';
            document.getElementById('profileEmail').value = this.currentUser.email || '';
            document.getElementById('profilePhone').value = this.currentUser.phone || '';
            
            if (this.currentRole === 'teacher') {
                document.getElementById('profileRoleLabel').style.display = 'block';
                document.getElementById('profileSubjectLabel').style.display = 'block';
                document.getElementById('profileExperienceLabel').style.display = 'block';
                document.getElementById('profileRole').value = 'Teacher';
                document.getElementById('profileSubject').value = this.currentUser.subject || '';
                document.getElementById('profileExperience').value = this.currentUser.experience || '';
            } else {
                document.getElementById('profileRoleLabel').style.display = 'none';
                document.getElementById('profileSubjectLabel').style.display = 'none';
                document.getElementById('profileExperienceLabel').style.display = 'none';
            }
        }
    }

    async saveProfile() {
        const profileData = {
            name: document.getElementById('profileName').value,
            email: document.getElementById('profileEmail').value,
            phone: document.getElementById('profilePhone').value
        };

        if (this.currentRole === 'teacher') {
            profileData.subject = document.getElementById('profileSubject').value;
            profileData.experience = document.getElementById('profileExperience').value;
        }

        try {
            await this.api.updateProfile(profileData);
            this.currentUser = { ...this.currentUser, ...profileData };
            localStorage.setItem('user', JSON.stringify(this.currentUser));
            this.closeProfileModal();
            alert('Profile updated successfully!');
        } catch (error) {
            console.error('Failed to update profile:', error);
            alert('Failed to update profile. Please try again.');
        }
    }

    logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        this.currentUser = null;
        this.currentRole = null;
        this.showAuth();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new UnifiedGramOthiApp();
});

// Global functions for HTML onclick handlers
function closeProfileModal() {
    if (window.app) {
        window.app.closeProfileModal();
    }
}

// Make profile modal accessible from header avatar
document.addEventListener('DOMContentLoaded', () => {
    const headerAvatar = document.querySelector('.header-avatar');
    if (headerAvatar) {
        headerAvatar.addEventListener('click', () => {
            if (window.app) {
                window.app.openProfileModal();
            }
        });
    }
});
