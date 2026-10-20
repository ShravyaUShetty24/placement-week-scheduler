-- ============================================
-- PLACEMENT WEEK SCHEDULER DATABASE
-- ============================================

-- Companies
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    priority TEXT NOT NULL CHECK(priority IN ('HIGH', 'MEDIUM', 'LOW')),
    cgpa_cutoff REAL NOT NULL,
    interview_duration INTEGER NOT NULL,
    panel_count INTEGER NOT NULL DEFAULT 1,
    arrival_time TEXT NOT NULL
);

-- Students
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    cgpa REAL NOT NULL,
    branch TEXT NOT NULL
);

-- Which students are shortlisted by which companies
CREATE TABLE IF NOT EXISTS shortlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,

    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (company_id) REFERENCES companies(id),

    UNIQUE(student_id, company_id)
);

-- Interview rooms
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL DEFAULT 1,
    available INTEGER NOT NULL DEFAULT 1
);

-- Scheduled interviews
CREATE TABLE IF NOT EXISTS interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,

    day INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,

    panel_id INTEGER NOT NULL DEFAULT 1,

    status TEXT NOT NULL DEFAULT 'SCHEDULED',

    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

-- Disruptions
CREATE TABLE IF NOT EXISTS disruptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    disruption_type TEXT NOT NULL,

    company_id INTEGER,
    student_id INTEGER,
    room_id INTEGER,

    description TEXT NOT NULL,

    old_value TEXT,
    new_value TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

-- Indexes to make conflict checking faster
CREATE INDEX IF NOT EXISTS idx_interviews_student
ON interviews(student_id);

CREATE INDEX IF NOT EXISTS idx_interviews_company
ON interviews(company_id);

CREATE INDEX IF NOT EXISTS idx_interviews_room
ON interviews(room_id);

CREATE INDEX IF NOT EXISTS idx_interviews_day_time
ON interviews(day, start_time);