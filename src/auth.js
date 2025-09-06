/**
 * Authentication System for GramOthi
 * Handles login/logout and role switching between Student and Teacher
 */

// Global state
let authState = {
    currentRole: 'student', // 'student' or 'teacher'
    isAuthenticated: false,
    user: null
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('GramOthi Auth System initialized');
    
    // Check if user is already authenticated
    checkAuthStatus();
    
    // Setup event listeners
    setupAuthEventListeners();
});

function setupAuthEventListeners() {
    // Role selection buttons
    const roleStudent = document.getElementById('roleStudent');
    const roleTeacher = document.getElementById('roleTeacher');
    
    if (roleStudent) {
        roleStudent.addEventListener('click', function() {
            selectRole('student');
        });
    }
    
    if (roleTeacher) {
        roleTeacher.addEventListener('click', function() {
            selectRole('teacher');
        });
    }
    
    // Authentication form
    const authForm = document.getElementById('authForm');
    if (authForm) {
        authForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleAuth();
        });
    }
}

function selectRole(role) {
    authState.currentRole = role;
    
    // Update button styles
    const roleStudent = document.getElementById('roleStudent');
    const roleTeacher = document.getElementById('roleTeacher');
    
    if (role === 'student') {
        roleStudent.className = 'btn';
        roleTeacher.className = 'btn-outline';
    } else {
        roleStudent.className = 'btn-outline';
        roleTeacher.className = 'btn';
    }
    
    // Update form title
    const formTitle = document.querySelector('#authForm h2') || document.querySelector('#authForm .title');
    if (formTitle) {
        formTitle.textContent = `Sign in as ${role.charAt(0).toUpperCase() + role.slice(1)}`;
    }
    
    console.log(`Role selected: ${role}`);
}

function handleAuth() {
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;
    
    if (!email || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    // Check if this is login or registration
    const isRegistration = checkIfRegistration();
    
    if (isRegistration) {
        registerUser(email, password);
    } else {
        loginUser(email, password);
    }
}

function checkIfRegistration() {
    // Simple check - if user clicks submit twice quickly, it's registration
    const now = Date.now();
    const lastSubmit = window.lastSubmitTime || 0;
    window.lastSubmitTime = now;
    
    return (now - lastSubmit) < 2000; // 2 seconds
}

async function loginUser(email, password) {
    try {
        showLoading(true);
        
        // Try to authenticate with backend
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            handleAuthSuccess(data);
        } else {
            // Fallback to local authentication for demo
            handleLocalAuth(email, password);
        }
    } catch (error) {
        console.error('Login error:', error);
        // Fallback to local authentication
        handleLocalAuth(email, password);
    } finally {
        showLoading(false);
    }
}

async function registerUser(email, password) {
    try {
        showLoading(true);
        
        // Try to register with backend
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: email.split('@')[0], // Use email prefix as name
                email: email,
                password: password,
                role: authState.currentRole
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            handleAuthSuccess(data);
        } else {
            // Fallback to local registration
            handleLocalRegistration(email, password);
        }
    } catch (error) {
        console.error('Registration error:', error);
        // Fallback to local registration
        handleLocalRegistration(email, password);
    } finally {
        showLoading(false);
    }
}

function handleLocalAuth(email, password) {
    // Local authentication for demo purposes
    const users = JSON.parse(localStorage.getItem('gramothi_users') || '[]');
    const user = users.find(u => u.email === email && u.password === password);
    
    if (user) {
        handleAuthSuccess({
            user: user,
            access_token: 'demo_token_' + Date.now()
        });
    } else {
        alert('Invalid credentials. Try registering first.');
    }
}

function handleLocalRegistration(email, password) {
    // Local registration for demo purposes
    const users = JSON.parse(localStorage.getItem('gramothi_users') || '[]');
    
    // Check if user already exists
    if (users.find(u => u.email === email)) {
        alert('User already exists. Try logging in.');
        return;
    }
    
    const newUser = {
        id: Date.now(),
        name: email.split('@')[0],
        email: email,
        password: password,
        role: authState.currentRole,
        createdAt: new Date().toISOString()
    };
    
    users.push(newUser);
    localStorage.setItem('gramothi_users', JSON.stringify(users));
    
    handleAuthSuccess({
        user: newUser,
        access_token: 'demo_token_' + Date.now()
    });
}

function handleAuthSuccess(authData) {
    authState.isAuthenticated = true;
    authState.user = authData.user;
    
    // Store auth data
    localStorage.setItem('gramothi_auth_token', authData.access_token);
    localStorage.setItem('gramothi_user', JSON.stringify(authData.user));
    
    // Redirect to appropriate dashboard
    redirectToDashboard();
}

function redirectToDashboard() {
    if (authState.currentRole === 'teacher') {
        // Redirect to teacher dashboard (could be a different URL)
        window.location.href = 'teacher.html';
    } else {
        // Redirect to student dashboard
        window.location.href = 'index.html';
    }
}

function checkAuthStatus() {
    const token = localStorage.getItem('gramothi_auth_token');
    const user = localStorage.getItem('gramothi_user');
    
    if (token && user) {
        try {
            authState.isAuthenticated = true;
            authState.user = JSON.parse(user);
            authState.currentRole = authState.user.role || 'student';
            
            // User is already authenticated, redirect to dashboard
            redirectToDashboard();
        } catch (error) {
            console.error('Error parsing stored user data:', error);
            clearAuthData();
        }
    }
}

function clearAuthData() {
    localStorage.removeItem('gramothi_auth_token');
    localStorage.removeItem('gramothi_user');
    authState.isAuthenticated = false;
    authState.user = null;
}

function showLoading(show) {
    const submitBtn = document.querySelector('#authForm button[type="submit"]');
    if (submitBtn) {
        if (show) {
            submitBtn.textContent = 'Signing in...';
            submitBtn.disabled = true;
        } else {
            submitBtn.textContent = 'Sign in';
            submitBtn.disabled = false;
        }
    }
}

// Logout function (can be called from other pages)
function logout() {
    clearAuthData();
    window.location.href = 'auth.html';
}

// Export functions for global access
window.GramOthiAuth = {
    logout,
    getCurrentUser: () => authState.user,
    isAuthenticated: () => authState.isAuthenticated,
    getCurrentRole: () => authState.currentRole
};
