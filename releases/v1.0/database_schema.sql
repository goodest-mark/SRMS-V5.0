CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_no TEXT UNIQUE,
        full_name TEXT,
        gender TEXT,
        class TEXT,
        stream TEXT,
        level TEXT
    , comments TEXT);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_no TEXT UNIQUE,
        full_name TEXT NOT NULL,
        gender TEXT,
        phone TEXT,
        email TEXT,
        status TEXT DEFAULT 'ACTIVE',
        level TEXT
    );
CREATE TABLE teacher_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        subject_name TEXT,
    
        UNIQUE(
            teacher_id,
            subject_name
        ),
    
        FOREIGN KEY(teacher_id)
        REFERENCES teachers(id)
        ON DELETE CASCADE
    );
CREATE TABLE teacher_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER,
    class_name TEXT,

    UNIQUE(
        teacher_id,
        class_name
    ),

    FOREIGN KEY(teacher_id)
    REFERENCES teachers(id)
    ON DELETE CASCADE
);
CREATE TABLE subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT,
        subject_short_name TEXT,
        level TEXT,
        subject_type TEXT,
        UNIQUE(subject_name, level)
    );
CREATE TABLE enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_no TEXT NOT NULL,
        subject_name TEXT NOT NULL,
        academic_year_id INTEGER,
        term_id INTEGER,
        UNIQUE(
            admission_no,
            subject_name,
            academic_year_id,
            term_id
        ),
        FOREIGN KEY (admission_no) REFERENCES students(admission_no) ON DELETE CASCADE,
        FOREIGN KEY (academic_year_id) REFERENCES academic_years(id) ON DELETE CASCADE,
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
    );
CREATE TABLE requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        academic_year_id INTEGER,
        term_id INTEGER,
        level TEXT,
        class_name TEXT,
        item_name TEXT,
        quantity TEXT,
        notes TEXT,
        FOREIGN KEY (academic_year_id) REFERENCES academic_years(id) ON DELETE CASCADE,
        FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
    );
CREATE TABLE academic_years (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year_name TEXT UNIQUE,
        is_active INTEGER DEFAULT 0
    );
CREATE TABLE terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term_name TEXT,
        academic_year_id INTEGER,
        is_active INTEGER DEFAULT 0,

        FOREIGN KEY (academic_year_id)
        REFERENCES academic_years(id)
        ON DELETE CASCADE
    );
CREATE TABLE exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_name TEXT,
        term_id INTEGER,
        level TEXT,
        status TEXT DEFAULT 'OPEN',

        FOREIGN KEY (term_id)
        REFERENCES terms(id)
        ON DELETE CASCADE
    );
CREATE TABLE results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_no TEXT,
        subject_name TEXT,
        marks INTEGER,
        exam_id INTEGER,
        UNIQUE(admission_no, subject_name, exam_id),

        FOREIGN KEY (admission_no)
        REFERENCES students(admission_no)
        ON DELETE CASCADE,

        FOREIGN KEY (exam_id)
        REFERENCES exams(id)
        ON DELETE CASCADE
    );
CREATE TABLE division_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT,
        division TEXT,
        min_points INTEGER,
        max_points INTEGER,
        UNIQUE(level, division)
    );
CREATE TABLE system_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT
    );
CREATE TABLE school_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school_name TEXT,
        school_motto TEXT,
        school_address TEXT,
        school_phone TEXT,
        school_email TEXT,
        school_website TEXT,
        head_teacher TEXT,
        academic_master TEXT,
        school_logo TEXT,
        school_stamp TEXT,
        login_background TEXT,
        dashboard_background TEXT,
        watermark_text TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE system_security (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_passcode TEXT,
        last_changed TEXT DEFAULT CURRENT_TIMESTAMP
    , security_question_1 TEXT, security_answer_1 TEXT, security_question_2 TEXT, security_answer_2 TEXT);
CREATE TABLE grade_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL,
        grade TEXT NOT NULL,
        min_mark INTEGER NOT NULL,
        max_mark INTEGER NOT NULL,
        points INTEGER NOT NULL,
        sort_order INTEGER DEFAULT 0,
        UNIQUE(level, grade)
    );
CREATE TABLE subject_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT UNIQUE,
        required_subjects INTEGER,
        best_of INTEGER,
        compulsory_passes INTEGER DEFAULT 0
    );
CREATE TABLE exam_remarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_no TEXT,
        exam_id INTEGER,
        teacher_remarks TEXT,
        headteacher_remarks TEXT,
        developmental_notes TEXT,
        UNIQUE(admission_no, exam_id),
        FOREIGN KEY(admission_no) REFERENCES students(admission_no) ON DELETE CASCADE,
        FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE
    );
