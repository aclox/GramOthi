/**
 * GramOthi API Client
 * Handles API communication for the student dashboard
 */

class GramOthiAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('auth_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Authentication methods
    async login(email, password) {
        const response = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (response.access_token) {
            this.token = response.access_token;
            this.user = response.user;
            
            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('user', JSON.stringify(this.user));
        }
        
        return response;
    }

    async register(name, email, password, role) {
        const response = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password, role })
        });
        
        if (response.access_token) {
            this.token = response.access_token;
            this.user = response.user;
            
            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('user', JSON.stringify(this.user));
        }
        
        return response;
    }

    async logout() {
        try {
            await this.request('/auth/logout', { method: 'POST' });
        } catch (error) {
            console.log('Logout request failed:', error);
        } finally {
            this.token = null;
            this.user = null;
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
        }
    }

    // Class management
    async getClasses() {
        return await this.request('/classes');
    }

    async joinClass(classCode) {
        return await this.request('/classes/join', {
            method: 'POST',
            body: JSON.stringify({ class_code: classCode })
        });
    }

    // Quiz management
    async getQuizzes(classId) {
        return await this.request(`/classes/${classId}/quizzes`);
    }

    async submitQuiz(quizId, answers) {
        return await this.request(`/quizzes/${quizId}/submit`, {
            method: 'POST',
            body: JSON.stringify({ answers })
        });
    }

    // File management
    async getSlides(classId) {
        return await this.request(`/media/slides?class_id=${classId}`);
    }

    // Progress tracking
    async getProgress() {
        return await this.request('/progress');
    }

    async updateProgress(progressData) {
        return await this.request('/progress/update', {
            method: 'POST',
            body: JSON.stringify(progressData)
        });
    }

    // Notifications
    async getNotifications() {
        return await this.request('/notifications');
    }

    async markNotificationRead(notificationId) {
        return await this.request(`/notifications/${notificationId}/read`, {
            method: 'PUT'
        });
    }
}

// Initialize global API client
window.api = new GramOthiAPI();
