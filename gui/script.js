// API Bridge using standard fetch calls
const api = {
    async check_saved_session() {
        const res = await fetch('/api/check_saved_session');
        return await res.json();
    },

    async authenticate(username, password) {
        const res = await fetch('/api/authenticate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        return await res.json();
    },

    async logout() {
        const res = await fetch('/api/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await res.json();
    },

    async update_all_user_data() {
        const res = await fetch('/api/update_all_user_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await res.json();
    },

    async get_score() {
        const res = await fetch('/api/get_score');
        return await res.json();
    },

    async progress_on_graduation() {
        const res = await fetch('/api/progress_on_graduation');
        return await res.json();
    },

    async student_info(withUpdate = false) {
        const res = await fetch(`/api/student_info?withUpdate=${Boolean(withUpdate)}`);
        return await res.json();
    },

    async study_progress_info(withUpdate = false) {
        const res = await fetch(`/api/study_progress_info?withUpdate=${Boolean(withUpdate)}`);
        return await res.json();
    },

    async required_courses_and_graduation_credits(withUpdate = false) {
        const res = await fetch(`/api/required_courses_and_graduation_credits?withUpdate=${Boolean(withUpdate)}`);
        return await res.json();
    },

    async all_years_course_grades(withUpdate = false) {
        const res = await fetch(`/api/all_years_course_grades?withUpdate=${Boolean(withUpdate)}`);
        return await res.json();
    },

    async missing_required_courses(withUpdate = false) {
        const res = await fetch(`/api/missing_required_courses?withUpdate=${Boolean(withUpdate)}`);
        return await res.json();
    },

    async course_selection_by_course_code(withUpdate = false) {
        const res = await fetch(`/api/course_selection_by_course_code?withUpdate=${Boolean(withUpdate)}`);
        return await res.json();
    },

    async courses_we_have_this_semester(withUpdate = false) {
        const res = await fetch(`/api/courses_we_have_this_semester?withUpdate=${Boolean(withUpdate)}`);
        return await res.json();
    },

    async schedule_my_class(schedule_data = null) {
        const res = await fetch('/api/schedule_my_class', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(schedule_data || {})
        });
        return await res.json();
    },

    async search_courses(options = {}) {
        const res = await fetch('/api/search_courses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(options || {})
        });
        return await res.json();
    }
};

// Polyfill window.pywebview.api for maximum compatibility
if (typeof window !== 'undefined') {
    if (!window.pywebview) {
        window.pywebview = { api };
    } else if (!window.pywebview.api) {
        window.pywebview.api = api;
    }
}

// Function to switch visible screen
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

// AUTO-RUN ON BOOT: Check session as soon as DOM or pywebview is ready
let appInitialized = false;
async function initApp() {
    if (appInitialized) return;
    appInitialized = true;

    try {
        const session = await api.check_saved_session();

        if (session && session.logged_in) {
            // User has a valid saved session -> Skip login!
            document.getElementById('user-display').innerText = session.username;
            showPage('page-dashboard');
            await getDashboardData();
            await updateProgressBar();
            await userInformation();
            loadCourses();
        } else {
            // No saved session -> Show Login page
            showPage('page-login');
        }
    } catch (err) {
        console.error("Initialization error:", err);
        showPage('page-login');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
window.addEventListener('pywebviewready', initApp);

async function updateUserLocalData() {
    document.getElementById('UpdataUserdataBtn').innerText = "Updating data, please wait...";
    try {
        await api.update_all_user_data();
        await getDashboardData();
        await updateProgressBar();
        await userInformation();
        await loadCourses();
    } catch (err) {
        console.error("Failed to update user data:", err);
    }
    document.getElementById('UpdataUserdataBtn').innerText = "Update User Data";
}

async function getDashboardData() {
    const data = await api.get_score();

    let table = `
        <table border="1" cellpadding="8" cellspacing="0">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Credits</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const [key, value] of Object.entries(data || {})) {
        table += `
            <tr>
                <td>${key.replace(/_/g, " ")}</td>
                <td>${value}</td>
            </tr>
        `;
    }

    table += `
            </tbody>
        </table>
    `;

    document.getElementById("dashboard-content").innerHTML = table;
}

async function updateRequiredCourses(withoutRefresh = false) {
    const data = await api.missing_required_courses(withoutRefresh);

    let table = `
        <table border="1" cellpadding="8" cellspacing="0">
            <thead>
                <tr>
                    <th>Grade</th>
                    <th>Course Name</th>
                    <th>Course Code</th>
                    <th>Specialization</th>
                    <th>Group</th>
                    <th>Credits Up</th>
                    <th>Credits Down</th>
                    <th>Note</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const course of (data || [])) {
        table += `
            <tr>
                <td>${course.grade || ''}</td>
                <td>${course.course_name || ''}</td>
                <td>${course.course_code || ''}</td>
                <td>${course.specialization || ''}</td>
                <td>${course.group || ''}</td>
                <td>${course.credits_up || ''}</td>
                <td>${course.credits_down || ''}</td>
                <td>${course.note || ''}</td>
            </tr>
        `;
    }

    table += `
            </tbody>
        </table>
    `;

    document.getElementById("required-courses-content").innerHTML = table;
    document.getElementById('update-required-courses-btn').innerText = "Update Required Courses";
}

async function updateProgressBar() {
    const data = await api.progress_on_graduation();
    const percent = data ? (data.total_percent || 0) : 0;
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = `${percent}%`;
    progressBar.innerText = `${percent}%`;
}

async function userInformation() {
    const data = await api.student_info();
    const infoDiv = document.getElementById('user-info');
    if (data && (data.name || data.id)) {
        infoDiv.innerHTML = `
            <p><strong>Name:</strong> ${data.name || ''} <strong>Student ID:</strong> ${data.id || ''} <strong>Department:</strong> ${data.grade || ''}</p>
        `;
    } else {
        infoDiv.innerHTML = '';
    }
}

async function updateAllGrades(withoutRefresh = false) {
    const data = await api.all_years_course_grades(withoutRefresh);

    const gradesDiv = document.getElementById("all-grades-content");

    const courses = (data && data.courses) ? data.courses : [];
    const rows = courses.map(course => `
        <tr>
            <td>${course.grade || ''}</td>
            <td>${course.course_name || ''}</td>
            <td>${course.course_code || ''}</td>
            <td>${course.specialization || ''}</td>
            <td>${course.group || ''}</td>
            <td>${course.credits_up || ''}</td>
            <td>${course.credits_down || ''}</td>
            <td>${course.requirement_type || ''}</td>
            <td>${course.status || ''}</td>
        </tr>
    `).join("");

    const totalEarned = data ? (data.total_earned_credits || 0) : 0;
    gradesDiv.innerHTML = `
        <p><strong>Total Earned Credits:</strong> ${totalEarned}</p>

        <table border="1" cellpadding="8" cellspacing="0">
            <thead>
                <tr>
                    <th>Grade</th>
                    <th>Course Name</th>
                    <th>Course Code</th>
                    <th>Specialization</th>
                    <th>Group</th>
                    <th>Credits Up</th>
                    <th>Credits Down</th>
                    <th>Requirement Type</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;

    document.getElementById("update-all-grades-btn").textContent = "Update All Grades";
}

async function updateMyClass(withoutRefresh = false) {
    const courses = await api.course_selection_by_course_code(withoutRefresh);

    const days = ["一", "二", "三", "四", "五"];
    const periods = [
        "01", "02", "03", "04", "05",
        "06", "07", "08", "09", "10",
        "11", "12", "13"
    ];

    // Initialize schedule
    const schedule = {};
    for (const day of days) {
        schedule[day] = {};
    }

    for (const course of (courses || [])) {
        if (!course.schedule) continue;
        for (const entry of course.schedule) {

            // Skip empty/invalid schedule entries
            if (!entry || entry.trim() === "/     /") continue;

            const match = entry.match(/^([一二三四五六日])\s*\/\s*([\d,]+)\s*\/\s*(.+)$/);

            if (!match) continue;

            const [, day, periodStr, room] = match;

            if (!schedule[day]) {
                schedule[day] = {};
            }

            for (const period of periodStr.split(",")) {
                const p = period.trim();

                if (!schedule[day][p]) {
                    schedule[day][p] = [];
                }

                schedule[day][p].push({
                    name: course.course_name,
                    teacher: (course.teachers || []).join(", "),
                    room: room.trim(),
                });
            }
        }
    }

    renderMyClass(schedule, days, periods);
}

function renderMyClass(schedule, days, periods) {
    const container = document.getElementById("my-class-content");

    let html = `
        <table class="my-class-table">
            <thead>
                <tr>
                    <th>Period</th>
                    ${days.map(day => `<th>${day}</th>`).join("")}
                </tr>
            </thead>
            <tbody>
    `;

    for (const period of periods) {
        html += `<tr><th>${period}</th>`;

        for (const day of days) {
            const classes = schedule[day]?.[period];

            if (classes && classes.length) {
                html += `<td class="has-class">`;

                for (const cls of classes) {
                    html += `
                        <div class="class-item">
                            <strong>${cls.name}</strong>
                            <small>${cls.teacher}</small>
                            <small>${cls.room}</small>
                        </div>
                    `;
                }

                html += `</td>`;
            } else {
                html += `<td></td>`;
            }
        }

        html += `</tr>`;
    }

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

function renderScheduleMyClass(schedule, days, periods) {
    const container = document.getElementById("schedule-my-class-content");

    let html = `
        <table class="my-class-table">
            <thead>
                <tr>
                    <th>Period</th>
                    ${days.map(day => `<th>${day}</th>`).join("")}
                </tr>
            </thead>
            <tbody>
    `;

    for (const period of periods) {
        html += `<tr><th>${period}</th>`;

        for (const day of days) {
            const classes = schedule[day]?.[period];

            if (classes && classes.length) {
                html += `<td class="has-class">`;

                for (const cls of classes) {
                    html += `
                        <div class="class-item">
                            <small>${cls.course_id}</small>
                            <strong>${cls.name}</strong>
                            <small>${cls.teacher}</small>
                            <small>${cls.room}</small>
                            <button onclick="updateScheduleMyClass({'options':'remove','course_id':'${cls.course_id}'})" class="small">remove</button>
                        </div>
                    `;
                }

                html += `</td>`;
            } else {
                html += `<td><button onclick="searchClassTimeClick({'day':'${day}','period':'${period}'})" class="small">+</button></td>`;
            }
        }

        html += `</tr>`;
    }

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
    document.getElementById('update-my-class-btn').innerText = 'Update My Class';
}

async function searchClassTimeClick(time) {
    const searchTime = `${time.day},${Number(time.period)}`;
    document.getElementById('search-time').value = searchTime;
    runSearch({
        times: searchTime,
    });
    showPage('find-class');
}

async function updateScheduleMyClass(options) {
    let courses = await api.schedule_my_class(options);

    if (!Array.isArray(courses)) {
        courses = [];
    }

    const days = ["一", "二", "三", "四", "五"];
    const periods = [
        "01", "02", "03", "04", "05",
        "06", "07", "08", "09", "10",
        "11", "12", "13"
    ];

    // Initialize empty schedule
    const schedule = {};
    for (const day of days) {
        schedule[day] = {};
    }

    for (const course of courses) {
        if (!course.schedule) continue;

        for (const entry of course.schedule) {

            if (!entry || entry.trim() === "/     /") continue;

            const match = entry.match(/^([一二三四五六日])\s*\/\s*([\d,]+)\s*\/\s*(.+)$/);

            if (!match) continue;

            const [, day, periodStr, room] = match;

            if (!schedule[day]) {
                schedule[day] = {};
            }

            for (const period of periodStr.split(",")) {
                const p = period.trim();

                if (!schedule[day][p]) {
                    schedule[day][p] = [];
                }

                schedule[day][p].push({
                    course_id: course.course_id,
                    name: course.course_name,
                    teacher: course.teachers?.join(", ") || "",
                    room: room.trim(),
                });
            }
        }
    }

    renderScheduleMyClass(schedule, days, periods);
    document.getElementById("load-my-class-section-btn").innerText = "Load My Class";
}

async function exportScheduleClass() {
    let exportSchedules = await api.schedule_my_class();

    if (!Array.isArray(exportSchedules)) {
        exportSchedules = [];
    }

    const exportText = exportSchedules
        .map(s => s.course_id)
        .join("\n");

    const container = document.getElementById("export-schedule-my-class");

    container.innerHTML = `
        <textarea id="export_textarea">${exportText}</textarea>
        <br>
        <button id="remove-export">Remove Export</button>
    `;

    document.getElementById("remove-export").addEventListener("click", () => {
        container.innerHTML = "";
    });
}

let courses = [];

// Load your large json once
async function loadCourses() {
    courses = await api.courses_we_have_this_semester();
    if (!Array.isArray(courses)) {
        courses = [];
    }
}

async function updateCourses() {
    document.getElementById('update-courses-btn').innerText = "loading";
    courses = await api.courses_we_have_this_semester(true);
    if (!Array.isArray(courses)) {
        courses = [];
    }
    document.getElementById('update-courses-btn').innerText = "Get the lastest Courses";
}

function normalize(text) {
    return String(text || "")
        .toLowerCase()
        .replace(/\s+/g, "");
}

async function searchCourses(options = {}) {
    const {
        title = "",
        times = "",
        required = "",
        dept_block = ""
    } = options;

    const titleQuery = normalize(title);
    const timeQuery = normalize(times);
    const deptQuery = normalize(dept_block);
    const requiredQuery = required.trim();

    return (courses || []).filter(course => {
        if (
            titleQuery &&
            !normalize(course.title).includes(titleQuery)
        ) {
            return false;
        }

        if (
            requiredQuery &&
            course.required !== requiredQuery
        ) {
            return false;
        }

        if (
            deptQuery &&
            !normalize(course.dept_block).includes(deptQuery)
        ) {
            return false;
        }

        if (timeQuery) {
            const searchTimes = timeQuery
                .split(/[,\s]+/)
                .map(t => t.trim())
                .filter(Boolean);

            const courseTokens = parseTimeTokens(course.times || []);

            if (!searchTimes.every(t => courseTokens.includes(normalize(t)))) {
                return false;
            }
        }

        return true;
    });
}

async function runSearch(options = {}) {
    const results = await searchCourses(options);

    const container = document.getElementById("search-result");
    if (!container) {
        console.error("search-result not found");
        return;
    }

    if (results.length === 0) {
        container.innerHTML = `
            <p>No courses found.</p>
        `;
        return;
    }

    container.innerHTML = `
        <h3>${results.length} courses found</h3>

        ${results.map(course => `
            <div class="course-card">
                <h3>
                    ${course.title || ''}
                </h3>
                <p>
                    Code: ${course.seq || ''}
                </p>
                <button onclick="updateScheduleMyClass({'options':'add','course_id':'${course.seq}'})" class="small">+</button>
                <p>
                    ${course.required || ''}
                    |
                    ${course.credits || ''} credits
                </p>
                <p>
                    Department:
                    ${course.dept_block || ''}
                </p>
                <p>
                    Teacher:
                    ${course.teacher || ''}
                </p>
                <p>
                    Time:
                    ${(course.times || []).join(", ")}
                </p>
            </div>
        `).join("")}
    `;
}

async function searchButtonClick() {
    runSearch({
        title: document.getElementById("search-title").value,
        times: document.getElementById("search-time").value,
        required: document.getElementById("search-required").value,
        dept_block: document.getElementById("search-dept").value
    });
}

async function setMyDepartment() {
    const myDepartmentinfo = await api.student_info();
    if (myDepartmentinfo && myDepartmentinfo.department) {
        document.getElementById("search-dept").value = myDepartmentinfo.department;
    }
}

function parseTimeTokens(times) {
    const tokens = [];
    for (const t of times) {
        const [day, periods] = t.split("/").map(s => s.trim());
        tokens.push(normalize(day));
        if (periods) {
            periods
                .split(",")
                .map(p => p.trim())
                .forEach(p => tokens.push(normalize(p)));
        }
    }
    return tokens;
}

// Login Handler
async function handleLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    document.getElementById('loginbtn').innerText = "Login check took time please wait";

    try {
        const success = await api.authenticate(user, pass);
        if (success) {
            document.getElementById('user-display').innerText = user;
            showPage('page-dashboard');
            await getDashboardData();
            await updateProgressBar();
            await userInformation();
            loadCourses();
        } else {
            document.getElementById('login-error').innerText = "Invalid credentials!";
        }
    } catch (err) {
        console.error("Login failed:", err);
        document.getElementById('login-error').innerText = "Login error occurred";
    } finally {
        document.getElementById('loginbtn').innerText = "Sign In";
    }
}

// Logout Handler
async function handleLogout() {
    try {
        await api.logout();
    } catch (err) {
        console.error("Logout error:", err);
    }
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    showPage('page-login');
}