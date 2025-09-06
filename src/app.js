/**
 * GramOthi Student Dashboard App
 * Main application logic for the student dashboard
 */

// Global state
let state = {
    user: null,
    classes: [],
    currentTab: 'dashboard',
    profileModal: null
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('GramOthi Student Dashboard initialized');
    
    // Initialize profile modal
    state.profileModal = document.getElementById('profileModal');
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize UI
    initializeUI();
    
    // Load user data
    loadUserData();
});

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
    
    // Join class form
    const joinClassForm = document.getElementById('joinClassForm');
    if (joinClassForm) {
        joinClassForm.addEventListener('submit', function(e) {
            e.preventDefault();
            joinClass();
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
    
    // Initialize calendar
    initializeCalendar();
    
    // Load upcoming tasks
    loadUpcomingTasks();
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
    
    state.currentTab = tabName;
}

function openProfileModal() {
    if (state.profileModal) {
        state.profileModal.showModal();
        loadProfileData();
    }
}

function closeProfileModal() {
    if (state.profileModal) {
        state.profileModal.close();
    }
}

function loadProfileData() {
    // Load user profile data into form
    const profileName = document.getElementById('profileName');
    const profileStudentId = document.getElementById('profileStudentId');
    const profileClassSection = document.getElementById('profileClassSection');
    const profileDob = document.getElementById('profileDob');
    const profilePhone = document.getElementById('profilePhone');
    
    if (state.user) {
        if (profileName) profileName.value = state.user.name || '';
        if (profileStudentId) profileStudentId.value = state.user.studentId || '';
        if (profileClassSection) profileClassSection.value = state.user.classSection || '';
        if (profileDob) profileDob.value = state.user.dob || '';
        if (profilePhone) profilePhone.value = state.user.phone || '';
    }
}

function saveProfile() {
    // Get form data
    const profileData = {
        name: document.getElementById('profileName')?.value || '',
        studentId: document.getElementById('profileStudentId')?.value || '',
        classSection: document.getElementById('profileClassSection')?.value || '',
        dob: document.getElementById('profileDob')?.value || '',
        phone: document.getElementById('profilePhone')?.value || ''
    };
    
    // Validate required fields
    if (!profileData.name) {
        alert('Please enter your full name');
        return;
    }
    
    // Save profile data
    try {
        // Update state
        state.user = { ...state.user, ...profileData };
        
        // Save to localStorage
        localStorage.setItem('gramothi_user', JSON.stringify(state.user));
        
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

function loadUserData() {
    // Load user data from localStorage
    const savedUser = localStorage.getItem('gramothi_user');
    if (savedUser) {
        try {
            state.user = JSON.parse(savedUser);
            updateUserDisplay();
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    } else {
        // Create default user if none exists
        state.user = {
            name: 'Student User',
            studentId: 'STU001',
            classSection: '10th A',
            dob: '',
            phone: ''
        };
        localStorage.setItem('gramothi_user', JSON.stringify(state.user));
        updateUserDisplay();
    }
}

function updateUserDisplay() {
    // Update header with user info
    const headerAvatar = document.querySelector('.header-avatar');
    if (headerAvatar && state.user) {
        headerAvatar.title = state.user.name || 'Profile';
    }
}

function joinClass() {
    const classCode = document.getElementById('classCode')?.value;
    if (!classCode) {
        alert('Please enter a class code');
        return;
    }
    
    // Add class to list
    const classList = document.getElementById('classList');
    if (classList) {
        const classItem = document.createElement('li');
        classItem.className = 'card';
        classItem.innerHTML = `
            <div class="class-info">
                <h3>Class ${classCode}</h3>
                <p>Joined on ${new Date().toLocaleDateString()}</p>
            </div>
            <div class="class-actions">
                <button class="btn btn-sm">Enter Class</button>
            </div>
        `;
        classList.appendChild(classItem);
    }
    
    // Clear form
    document.getElementById('classCode').value = '';
    
    alert(`Successfully joined class ${classCode}!`);
}

function performSearch() {
    const searchTerm = document.getElementById('globalSearch')?.value;
    if (!searchTerm) {
        alert('Please enter a search term');
        return;
    }
    
    // Simple search functionality
    console.log('Searching for:', searchTerm);
    alert(`Searching for: ${searchTerm}`);
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Clear user data
        localStorage.removeItem('gramothi_user');
        state.user = null;
        
        // Redirect to login or reload
        window.location.reload();
    }
}

function initializeCalendar() {
    const calTitle = document.getElementById('calTitle');
    const calGrid = document.getElementById('calGrid');
    
    if (calTitle && calGrid) {
        const now = new Date();
        const month = now.toLocaleDateString('en-US', { month: 'long' });
        const year = now.getFullYear();
        
        calTitle.textContent = `${month} ${year}`;
        
        // Simple calendar grid
        calGrid.innerHTML = `
            <div class="cal-day">1</div>
            <div class="cal-day">2</div>
            <div class="cal-day">3</div>
            <div class="cal-day">4</div>
            <div class="cal-day">5</div>
            <div class="cal-day">6</div>
            <div class="cal-day">7</div>
            <div class="cal-day">8</div>
            <div class="cal-day">9</div>
            <div class="cal-day">10</div>
            <div class="cal-day">11</div>
            <div class="cal-day">12</div>
            <div class="cal-day">13</div>
            <div class="cal-day">14</div>
            <div class="cal-day">15</div>
            <div class="cal-day">16</div>
            <div class="cal-day">17</div>
            <div class="cal-day">18</div>
            <div class="cal-day">19</div>
            <div class="cal-day">20</div>
            <div class="cal-day">21</div>
            <div class="cal-day">22</div>
            <div class="cal-day">23</div>
            <div class="cal-day">24</div>
            <div class="cal-day">25</div>
            <div class="cal-day">26</div>
            <div class="cal-day">27</div>
            <div class="cal-day">28</div>
            <div class="cal-day">29</div>
            <div class="cal-day">30</div>
            <div class="cal-day">31</div>
        `;
    }
}

function loadUpcomingTasks() {
    const upcomingList = document.getElementById('upcomingList');
    if (upcomingList) {
        // Sample upcoming tasks
        const tasks = [
            'Math Quiz - Tomorrow 10:00 AM',
            'Science Assignment - Due Friday',
            'English Essay - Next Monday'
        ];
        
        upcomingList.innerHTML = tasks.map(task => `<li>${task}</li>`).join('');
    }
}

// Utility functions
function showNotification(message, type = 'info') {
    // Simple notification system
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #333;
        color: white;
        padding: 10px 20px;
        border-radius: 4px;
        z-index: 1000;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Export functions for global access
window.GramOthiApp = {
    openProfileModal,
    closeProfileModal,
    saveProfile,
    switchTab,
    joinClass,
    performSearch,
    logout
};
