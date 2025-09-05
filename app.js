// Educator Dashboard - Extracted JS

// State (in-memory)
const state = {
    uploadedFiles: [], // { id, name, size, type, addedAt }
    notes: [], // { id, name, size, type, addedAt }
    quizzes: [], // { id, title, status, questions, attempts, avgScore, pending }
    students: [
        {
            id: 'stu001',
            firstName: 'Alex',
            lastName: 'Johnson',
            email: 'alex.johnson@email.com',
            phone: '+1 (555) 123-4567',
            studentId: 'STU001',
            grade: 'A+',
            subjects: 'Math, Science',
            notes: 'Excellent student, very engaged',
            progress: 95,
            lastQuiz: 95,
            quizResults: [
                { id: 'q1', title: 'Algebra Basics', score: 95, date: '2024-01-15' },
                { id: 'q2', title: 'Geometry Fundamentals', score: 92, date: '2024-01-20' },
                { id: 'q3', title: 'Statistics Intro', score: 98, date: '2024-01-25' }
            ],
            attendance: {
                present: 18,
                absent: 2,
                partial: 1
            },
            studentNotes: [
                { id: 'n1', content: 'Shows great potential in mathematics', date: '2024-01-10', author: 'Dr. Johnson' },
                { id: 'n2', content: 'Helped other students with homework', date: '2024-01-20', author: 'Dr. Johnson' }
            ]
        },
        {
            id: 'stu002',
            firstName: 'Sarah',
            lastName: 'Miller',
            email: 'sarah.miller@email.com',
            phone: '+1 (555) 234-5678',
            studentId: 'STU002',
            grade: 'A',
            subjects: 'Math, English',
            notes: 'Consistent performer',
            progress: 88,
            lastQuiz: 88,
            quizResults: [
                { id: 'q1', title: 'Algebra Basics', score: 88, date: '2024-01-15' },
                { id: 'q2', title: 'Geometry Fundamentals', score: 85, date: '2024-01-20' },
                { id: 'q3', title: 'Statistics Intro', score: 91, date: '2024-01-25' }
            ],
            attendance: {
                present: 19,
                absent: 1,
                partial: 1
            },
            studentNotes: [
                { id: 'n1', content: 'Good understanding of concepts', date: '2024-01-12', author: 'Dr. Johnson' }
            ]
        },
        {
            id: 'stu003',
            firstName: 'Mike',
            lastName: 'Davis',
            email: 'mike.davis@email.com',
            phone: '+1 (555) 345-6789',
            studentId: 'STU003',
            grade: 'B+',
            subjects: 'Science, Math',
            notes: 'Needs more practice with problem solving',
            progress: 78,
            lastQuiz: 82,
            quizResults: [
                { id: 'q1', title: 'Algebra Basics', score: 75, date: '2024-01-15' },
                { id: 'q2', title: 'Geometry Fundamentals', score: 80, date: '2024-01-20' },
                { id: 'q3', title: 'Statistics Intro', score: 85, date: '2024-01-25' }
            ],
            attendance: {
                present: 17,
                absent: 3,
                partial: 1
            },
            studentNotes: [
                { id: 'n1', content: 'Improving steadily', date: '2024-01-18', author: 'Dr. Johnson' }
            ]
        }
    ],
    isLive: false,
    isRecording: false,
    recordings: [], // { id, title, startedAt }
    profile: {
        name: "Dr. Sarah Johnson",
        designation: "Senior Mathematics Professor",
        joinDate: "Jan 2020",
        subjects: "Math, Statistics",
        qualification: "PhD Mathematics"
    },
    currentStudent: null, // Currently selected student for details modal
    filteredStudents: [] // Filtered students list
};

// Utilities
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const formatBytes = bytes => {
    if (!bytes && bytes !== 0) return "";
    const sizes = ['B','KB','MB','GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const val = bytes / Math.pow(1024, i);
    return `${val.toFixed(val >= 100 ? 0 : val >= 10 ? 1 : 2)} ${sizes[i]}`;
};
const nowLabel = () => new Date().toLocaleString();
const uid = () => Math.random().toString(36).slice(2, 9);

// Navigation and sections
function setActiveSection(id) {
    // highlight sidebar
    $$(".nav button").forEach(b => b.classList.toggle("active", b.dataset.target === id));
    // show section
    $$(".section").forEach(s => s.classList.toggle("active", s.id === id));
    // update quick actions when switching
    updateStatusChips();
    // close mobile sidebar
    $('#sidebar')?.classList.remove('open');
}

function updateStatusChips() {
    $('#liveStatusChip').textContent = `Live: ${state.isLive ? 'Online' : 'Offline'}`;
    $('#recordQuickToggle').textContent = `Recording: ${state.isRecording ? 'On' : 'Off'}`;
}

// Dashboard
function renderDashboard() {
    $('#statFiles').textContent = state.uploadedFiles.length;
    $('#statRecordings').textContent = state.recordings.length;
    $('#statStudents').textContent = state.students.length;
    $('#statQuizzes').textContent = state.quizzes.length;

    const recentUploads = $('#recentUploads');
    if (state.uploadedFiles.length === 0) {
        recentUploads.classList.add('muted');
        recentUploads.textContent = 'No files uploaded yet.';
    } else {
        recentUploads.classList.remove('muted');
        recentUploads.innerHTML = '';
        state.uploadedFiles.slice(-5).reverse().forEach(f => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="meta">
                    <span>📄</span>
                    <div>
                        <div style="font-weight:700">${f.name}</div>
                        <div class="muted">${formatBytes(f.size)} • ${f.type || 'file'} • ${new Date(f.addedAt).toLocaleDateString()}</div>
                    </div>
                </div>
                <span class="pill">NEW</span>
            `;
            recentUploads.appendChild(item);
        });
    }

    const recentRecs = $('#recentRecordings');
    if (state.recordings.length === 0) {
        recentRecs.classList.add('muted');
        recentRecs.textContent = 'No recordings yet.';
    } else {
        recentRecs.classList.remove('muted');
        recentRecs.innerHTML = '';
        state.recordings.slice(-5).reverse().forEach(r => {
            const item = document.createElement('div');
            item.className = 'list-item';
            item.innerHTML = `
                <div class="meta">
                    <span>🎥</span>
                    <div>
                        <div style="font-weight:700">${r.title}</div>
                        <div class="muted">${new Date(r.startedAt).toLocaleString()}</div>
                    </div>
                </div>
                <span class="pill">REC</span>
            `;
            recentRecs.appendChild(item);
        });
    }
}

// Uploads
function addSelectedFiles(files) {
    const accepted = ['application/pdf', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'];
    Array.from(files).forEach(file => {
        // Allow by extension if type missing
        const isAccepted = accepted.includes(file.type) || /\.(pdf|ppt|pptx)$/i.test(file.name);
        if (!isAccepted) return; // ignore unsupported
        state.uploadedFiles.push({ id: uid(), name: file.name, size: file.size, type: file.type, addedAt: Date.now() });
    });
    renderFilesList();
    renderDashboard();
}

function renderFilesList() {
    const list = $('#filesList');
    list.innerHTML = '';
    if (state.uploadedFiles.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'muted';
        empty.textContent = 'No files yet. Use the file picker to add PDFs/PPTs.';
        list.appendChild(empty);
        return;
    }
    state.uploadedFiles.slice().reverse().forEach(file => {
        const row = document.createElement('div');
        row.className = 'list-item';
        row.innerHTML = `
            <div class="meta">
                <span>📄</span>
                <div>
                    <div style="font-weight:700">${file.name}</div>
                    <div class="muted">${formatBytes(file.size)} • added ${nowLabel()}</div>
                </div>
            </div>
            <div class="row">
                <span class="pill">${/\.pdf$/i.test(file.name) ? 'PDF' : 'PPT'}</span>
                <button class="btn" data-action="delete" data-id="${file.id}">Delete</button>
            </div>
        `;
        list.appendChild(row);
    });

    // attach delete handlers
    $$("button[data-action='delete']", list).forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const idx = state.uploadedFiles.findIndex(f => f.id === id);
            if (idx !== -1) {
                state.uploadedFiles.splice(idx, 1);
                renderFilesList();
                renderDashboard();
            }
        });
    });
}

// Profile management
function updateProfileDisplay() {
    $('#profileName').textContent = state.profile.name;
    $('#profileDesignation').textContent = state.profile.designation;
    $('#profileJoinDate').textContent = state.profile.joinDate;
    $('#profileSubjects').textContent = state.profile.subjects;
    $('#profileQualification').textContent = state.profile.qualification;
    
    // Update avatar initials
    const initials = state.profile.name.split(' ').map(n => n[0]).join('').toUpperCase();
    $('#profileAvatar').textContent = initials;
}

function startProfileEdit() {
    $('#profileDisplay').style.display = 'none';
    $('#profileEditForm').style.display = 'block';
    $('#profileCard').classList.add('editing');
    
    // Populate form with current values
    $('#editName').value = state.profile.name;
    $('#editDesignation').value = state.profile.designation;
    $('#editJoinDate').value = state.profile.joinDate;
    $('#editSubjects').value = state.profile.subjects;
    $('#editQualification').value = state.profile.qualification;
}

function cancelProfileEdit() {
    $('#profileDisplay').style.display = 'flex';
    $('#profileEditForm').style.display = 'none';
    $('#profileCard').classList.remove('editing');
}

function saveProfile() {
    // Update state
    state.profile.name = $('#editName').value.trim();
    state.profile.designation = $('#editDesignation').value.trim();
    state.profile.joinDate = $('#editJoinDate').value.trim();
    state.profile.subjects = $('#editSubjects').value.trim();
    state.profile.qualification = $('#editQualification').value.trim();
    
    // Update display
    updateProfileDisplay();
    
    // Save to localStorage
    storage.set('profile', state.profile);
    
    // Switch back to display mode
    cancelProfileEdit();
}

function loadProfile() {
    const saved = storage.get('profile', state.profile);
    state.profile = { ...state.profile, ...saved };
    updateProfileDisplay();
}

// Notes management
function addNotes(files) {
    const accepted = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    Array.from(files).forEach(file => {
        const isAccepted = accepted.includes(file.type) || /\.(pdf|doc|docx|txt)$/i.test(file.name);
        if (!isAccepted) return;
        state.notes.push({ id: uid(), name: file.name, size: file.size, type: file.type, addedAt: Date.now() });
    });
    renderNotesList();
}

function renderNotesList() {
    const list = $('#notesList');
    list.innerHTML = '';
    if (state.notes.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'muted';
        empty.textContent = 'No notes uploaded yet.';
        list.appendChild(empty);
        return;
    }
    state.notes.slice().reverse().forEach(note => {
        const row = document.createElement('div');
        row.className = 'list-item';
        row.innerHTML = `
            <div class="meta">
                <span>📄</span>
                <div>
                    <div style="font-weight:700">${note.name}</div>
                    <div class="muted">${formatBytes(note.size)} • uploaded ${nowLabel()}</div>
                </div>
            </div>
            <div class="row">
                <span class="pill">${/\.pdf$/i.test(note.name) ? 'PDF' : /\.doc$/i.test(note.name) ? 'DOC' : 'TXT'}</span>
                <button class="btn" data-action="delete-note" data-id="${note.id}">Delete</button>
            </div>
        `;
        list.appendChild(row);
    });

    $$("button[data-action='delete-note']", list).forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const idx = state.notes.findIndex(n => n.id === id);
            if (idx !== -1) {
                state.notes.splice(idx, 1);
                renderNotesList();
            }
        });
    });
}

// Quiz management
function createQuiz() {
    const title = $('#quizTitleInput').value.trim();
    if (!title) return;
    
    state.quizzes.push({
        id: uid(),
        title: title,
        status: 'Draft',
        questions: 0,
        attempts: 0,
        avgScore: 0,
        pending: 0,
        createdAt: Date.now()
    });
    
    $('#quizTitleInput').value = '';
    renderQuizzesList();
}

function renderQuizzesList() {
    const list = $('#quizzesList');
    list.innerHTML = '';
    if (state.quizzes.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'muted';
        empty.textContent = 'No quizzes created yet.';
        list.appendChild(empty);
        return;
    }
    state.quizzes.slice().reverse().forEach(quiz => {
        const row = document.createElement('div');
        row.className = 'quiz-card';
        row.innerHTML = `
            <div class="quiz-header">
                <h4 class="quiz-title">${quiz.title}</h4>
                <span class="pill">${quiz.status}</span>
            </div>
            <div class="quiz-meta">
                <span>📅 Created: ${new Date(quiz.createdAt).toLocaleDateString()}</span>
                <span>⏱️ Duration: 30 min</span>
                <span>❓ Questions: ${quiz.questions}</span>
            </div>
            <div class="quiz-stats">
                <div class="quiz-stat">
                    <div class="num">${quiz.attempts}</div>
                    <div class="label">Attempts</div>
                </div>
                <div class="quiz-stat">
                    <div class="num">${quiz.avgScore || '-'}</div>
                    <div class="label">Avg Score</div>
                </div>
                <div class="quiz-stat">
                    <div class="num">${quiz.pending}</div>
                    <div class="label">Pending</div>
                </div>
            </div>
        `;
        list.appendChild(row);
    });
}

// Live and recording
function setLive(live) {
    state.isLive = !!live;
    $('#liveToggle').classList.toggle('active', state.isLive);
    $('#liveToggle').setAttribute('aria-pressed', String(state.isLive));
    updateStatusChips();
}
function setRecording(rec) {
    // When stopping a recording, add an entry
    const wasRecording = state.isRecording;
    state.isRecording = !!rec;
    $('#recordBtn').textContent = state.isRecording ? 'Stop Recording' : 'Start Recording';
    $('#recordQuickToggle').textContent = `Recording: ${state.isRecording ? 'On' : 'Off'}`;
    if (wasRecording && !state.isRecording) {
        state.recordings.push({ id: uid(), title: `Lecture • ${nowLabel()}` , startedAt: Date.now() });
        renderRecordingsList();
        renderDashboard();
    }
}

function renderRecordingsList() {
    const list = $('#recordingsList');
    list.innerHTML = '';
    if (state.recordings.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'muted';
        empty.textContent = 'No recordings yet. Use Start/Stop recording to add one.';
        list.appendChild(empty);
        return;
    }
    state.recordings.slice().reverse().forEach(rec => {
        const row = document.createElement('div');
        row.className = 'list-item';
        row.innerHTML = `
            <div class="meta">
                <span>🎥</span>
                <div>
                    <div style="font-weight:700">${rec.title}</div>
                    <div class="muted">${new Date(rec.startedAt).toLocaleString()}</div>
                </div>
            </div>
            <button class="btn" data-action="delete-rec" data-id="${rec.id}">Delete</button>
        `;
        list.appendChild(row);
    });

    $$("button[data-action='delete-rec']", list).forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const idx = state.recordings.findIndex(r => r.id === id);
            if (idx !== -1) {
                state.recordings.splice(idx, 1);
                renderRecordingsList();
                renderDashboard();
            }
        });
    });
}

// Theme and accent persistence
const storage = {
    get(key, fallback) {
        try { const v = localStorage.getItem(key); return v == null ? fallback : JSON.parse(v); } catch { return fallback; }
    },
    set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch {} }
};

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const isDark = theme === 'dark';
    $('#themeToggle').classList.toggle('active', isDark);
    $('#themeToggle').setAttribute('aria-pressed', String(isDark));
}

function applyAccent(hex) {
    const root = document.documentElement;
    root.style.setProperty('--accent', hex);
    root.style.setProperty('--accent-strong', hex);
    // mark swatch
    $$('#accentSwatches .swatch').forEach(s => s.classList.toggle('active', s.dataset.accent === hex));
}

// Student Management Functions
function renderStudentsList() {
    const list = $('#studentsList');
    if (!list) return;

    const studentsToShow = state.filteredStudents.length > 0 ? state.filteredStudents : state.students;
    
    list.innerHTML = '';
    
    studentsToShow.forEach(student => {
        const initials = `${student.firstName[0]}${student.lastName[0]}`.toUpperCase();
        const row = document.createElement('div');
        row.className = 'student-card';
        row.setAttribute('data-student-id', student.id);
        row.innerHTML = `
            <div class="student-avatar">${initials}</div>
            <div class="student-info">
                <h4>${student.firstName} ${student.lastName}</h4>
                <div class="grade">Grade: ${student.grade} | Last Quiz: ${student.lastQuiz}%</div>
            </div>
            <div class="student-progress">
                <div class="progress-label">Overall Progress</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${student.progress}%"></div>
                </div>
            </div>
        `;
        list.appendChild(row);
    });

    // Add click listeners to student cards
    $$('.student-card', list).forEach(card => {
        card.addEventListener('click', () => {
            const studentId = card.getAttribute('data-student-id');
            const student = state.students.find(s => s.id === studentId);
            if (student) {
                showStudentDetails(student);
            }
        });
    });
}

function showStudentDetails(student) {
    state.currentStudent = student;
    
    // Update modal content
    $('#studentDetailsTitle').textContent = `${student.firstName} ${student.lastName}`;
    $('#studentDetailsName').textContent = `${student.firstName} ${student.lastName}`;
    $('#studentDetailsEmail').textContent = student.email;
    $('#studentDetailsPhone').textContent = student.phone;
    $('#studentDetailsId').textContent = `ID: ${student.studentId}`;
    
    // Update avatar
    const initials = `${student.firstName[0]}${student.lastName[0]}`.toUpperCase();
    $('#studentDetailsAvatar').textContent = initials;
    
    // Update overview stats
    $('#overallGrade').textContent = student.grade;
    $('#averageScore').textContent = `${student.progress}%`;
    $('#quizzesCompleted').textContent = student.quizResults.length;
    
    // Show modal
    $('#studentDetailsModal').classList.add('show');
    
    // Load tab content
    loadStudentTabContent('overview');
}

function loadStudentTabContent(tabName) {
    if (!state.currentStudent) return;
    
    const student = state.currentStudent;
    
    // Hide all tab panes
    $$('.tab-pane').forEach(pane => pane.classList.remove('active'));
    $$('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    $(`#${tabName}`).classList.add('active');
    $(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
    
    switch (tabName) {
        case 'overview':
            loadOverviewTab(student);
            break;
        case 'quizzes':
            loadQuizzesTab(student);
            break;
        case 'attendance':
            loadAttendanceTab(student);
            break;
        case 'notes':
            loadNotesTab(student);
            break;
    }
}

function loadOverviewTab(student) {
    // This is already handled in showStudentDetails
}

function loadQuizzesTab(student) {
    const container = $('#studentQuizResults');
    if (!container) return;
    
    container.innerHTML = '';
    
    student.quizResults.forEach(quiz => {
        const item = document.createElement('div');
        item.className = 'quiz-result-item';
        item.innerHTML = `
            <div class="quiz-result-info">
                <h4>${quiz.title}</h4>
                <div class="quiz-result-meta">Completed: ${quiz.date}</div>
            </div>
            <div class="quiz-result-score">${quiz.score}%</div>
        `;
        container.appendChild(item);
    });
}

function loadAttendanceTab(student) {
    const container = $('#attendanceCalendar');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Generate calendar for current month
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startDay = firstDay.getDay();
    
    // Add day headers
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
        const header = document.createElement('div');
        header.className = 'attendance-day';
        header.textContent = day;
        header.style.fontWeight = '700';
        header.style.color = 'var(--color-text-muted)';
        container.appendChild(header);
    });
    
    // Add empty cells for days before month starts
    for (let i = 0; i < startDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'attendance-day';
        container.appendChild(empty);
    }
    
    // Add days of month
    for (let day = 1; day <= daysInMonth; day++) {
        const dayEl = document.createElement('div');
        dayEl.className = 'attendance-day';
        dayEl.textContent = day;
        
        // Mark today
        if (day === now.getDate()) {
            dayEl.classList.add('today');
        }
        
        // Simulate attendance data (in real app, this would come from backend)
        if (day <= now.getDate()) {
            const random = Math.random();
            if (random < 0.8) {
                dayEl.classList.add('present');
            } else if (random < 0.9) {
                dayEl.classList.add('partial');
            } else {
                dayEl.classList.add('absent');
            }
        } else {
            dayEl.classList.add('future');
        }
        
        container.appendChild(dayEl);
    }
}

function loadNotesTab(student) {
    const container = $('#studentNotesList');
    if (!container) return;
    
    container.innerHTML = '';
    
    student.studentNotes.forEach(note => {
        const item = document.createElement('div');
        item.className = 'note-item';
        item.innerHTML = `
            <div class="note-header">
                <div class="note-date">${note.date} - ${note.author}</div>
            </div>
            <div class="note-content">${note.content}</div>
        `;
        container.appendChild(item);
    });
}

function addStudent(studentData) {
    const newStudent = {
        id: uid(),
        ...studentData,
        progress: 0,
        lastQuiz: 0,
        quizResults: [],
        attendance: { present: 0, absent: 0, partial: 0 },
        studentNotes: []
    };
    
    state.students.push(newStudent);
    renderStudentsList();
    renderDashboard();
    
    // Close modal
    $('#addStudentModal').classList.remove('show');
    
    // Reset form
    $('#addStudentForm').reset();
}

function deleteStudent(studentId) {
    if (confirm('Are you sure you want to delete this student? This action cannot be undone.')) {
        const index = state.students.findIndex(s => s.id === studentId);
        if (index !== -1) {
            state.students.splice(index, 1);
            renderStudentsList();
            renderDashboard();
            $('#studentDetailsModal').classList.remove('show');
        }
    }
}

function addStudentNote(noteContent) {
    if (!state.currentStudent || !noteContent.trim()) return;
    
    const newNote = {
        id: uid(),
        content: noteContent.trim(),
        date: new Date().toISOString().split('T')[0],
        author: state.profile.name
    };
    
    state.currentStudent.studentNotes.push(newNote);
    loadNotesTab(state.currentStudent);
}

function filterStudents() {
    const searchTerm = $('#studentSearch')?.value.toLowerCase() || '';
    const gradeFilter = $('#gradeFilter')?.value || '';
    
    state.filteredStudents = state.students.filter(student => {
        const matchesSearch = !searchTerm || 
            student.firstName.toLowerCase().includes(searchTerm) ||
            student.lastName.toLowerCase().includes(searchTerm) ||
            student.email.toLowerCase().includes(searchTerm) ||
            student.studentId.toLowerCase().includes(searchTerm);
        
        const matchesGrade = !gradeFilter || student.grade === gradeFilter;
        
        return matchesSearch && matchesGrade;
    });
    
    renderStudentsList();
}

// Modal Management
function showModal(modalId) {
    $(`#${modalId}`).classList.add('show');
}

function hideModal(modalId) {
    $(`#${modalId}`).classList.remove('show');
}

// Init
function init() {
    // Navigation clicks
    $$('#nav button, .actions .btn').forEach(btn => {
        const target = btn.getAttribute('data-target');
        if (target) {
            btn.addEventListener('click', () => setActiveSection(target));
        }
    });

    // Sidebar nav behavior
    $$('#nav button').forEach(btn => {
        btn.addEventListener('click', () => setActiveSection(btn.dataset.target));
    });

    // Mobile sidebar
    $('#hamburger').addEventListener('click', () => $('#sidebar').classList.toggle('open'));

    // File upload
    $('#uploadBtn').addEventListener('click', () => {
        const files = $('#fileInput').files;
        addSelectedFiles(files);
        $('#fileInput').value = '';
    });

    // Notes upload
    $('#notesUpload').addEventListener('click', () => $('#notesInput').click());
    $('#notesInput').addEventListener('change', (e) => {
        addNotes(e.target.files);
        e.target.value = '';
    });

    // Quiz creation
    $('#createQuizBtn').addEventListener('click', createQuiz);
    $('#quizTitleInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') createQuiz();
    });

    // Profile editing
    $('#editProfileBtn').addEventListener('click', startProfileEdit);
    $('#cancelEditBtn').addEventListener('click', cancelProfileEdit);
    $('#saveProfileBtn').addEventListener('click', saveProfile);

    // Live/Recording toggles
    $('#liveToggle').addEventListener('click', () => setLive(!state.isLive));
    $('#recordBtn').addEventListener('click', () => setRecording(!state.isRecording));
    $('#recordQuickToggle').addEventListener('click', () => setRecording(!state.isRecording));

    // Theme toggle (quick)
    $('#themeQuickToggle').addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next); storage.set('theme', next);
    });
    // Theme toggle (settings)
    $('#themeToggle').addEventListener('click', () => {
        const isActive = $('#themeToggle').classList.contains('active');
        const next = isActive ? 'light' : 'dark';
        applyTheme(next); storage.set('theme', next);
    });

    // Accent swatches
    $$('#accentSwatches .swatch').forEach(s => {
        s.addEventListener('click', () => { applyAccent(s.dataset.accent); storage.set('accent', s.dataset.accent); });
    });

    // Load persisted theme/accent
    applyTheme(storage.get('theme', 'light'));
    applyAccent(storage.get('accent', getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()));

    // Load profile
    loadProfile();

    // Initial renders
    // Student Management Event Listeners
    $('#addStudentBtn').addEventListener('click', () => showModal('addStudentModal'));
    $('#closeAddStudentModal').addEventListener('click', () => hideModal('addStudentModal'));
    $('#cancelAddStudent').addEventListener('click', () => hideModal('addStudentModal'));
    
    $('#addStudentForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = {
            firstName: $('#studentFirstName').value.trim(),
            lastName: $('#studentLastName').value.trim(),
            email: $('#studentEmail').value.trim(),
            phone: $('#studentPhone').value.trim(),
            studentId: $('#studentId').value.trim(),
            grade: $('#studentGrade').value,
            subjects: $('#studentSubjects').value.trim(),
            notes: $('#studentNotes').value.trim()
        };
        
        // Basic validation
        if (!formData.firstName || !formData.lastName || !formData.email || !formData.studentId) {
            alert('Please fill in all required fields.');
            return;
        }
        
        // Check if student ID already exists
        if (state.students.some(s => s.studentId === formData.studentId)) {
            alert('A student with this ID already exists.');
            return;
        }
        
        addStudent(formData);
    });
    
    // Student Details Modal
    $('#closeStudentDetailsModal').addEventListener('click', () => hideModal('studentDetailsModal'));
    $('#deleteStudentBtn').addEventListener('click', () => {
        if (state.currentStudent) {
            deleteStudent(state.currentStudent.id);
        }
    });
    
    // Student Details Tabs
    $$('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            loadStudentTabContent(tabName);
        });
    });
    
    // Student Search and Filter
    $('#studentSearch').addEventListener('input', filterStudents);
    $('#gradeFilter').addEventListener('change', filterStudents);
    
    // Add Student Note
    $('#addStudentNoteBtn').addEventListener('click', () => {
        const noteContent = $('#newStudentNote').value.trim();
        if (noteContent) {
            addStudentNote(noteContent);
            $('#newStudentNote').value = '';
        }
    });
    
    // Modal backdrop clicks
    $$('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });
    
    renderFilesList();
    renderNotesList();
    renderQuizzesList();
    renderRecordingsList();
    renderStudentsList();
    renderDashboard();
    updateStatusChips();
}

document.addEventListener('DOMContentLoaded', init);


