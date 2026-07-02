import sqlite3
import hashlib
import re
import secrets

DB_NAME = "srms.db"

# Whitelist pattern for identifiers used in migrations
_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_SAFE_DEFINITION = re.compile(r"^[a-zA-Z_ \"]+$")


def _validate_identifier(name):
    """Ensure a column/table name is a safe SQL identifier."""
    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")
    return name


def _validate_definition(defn):
    """Ensure a column definition contains only safe characters."""
    if not _SAFE_DEFINITION.match(defn):
        raise ValueError(f"Unsafe column definition: {defn!r}")
    return defn


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db():
    conn = connect()
    cur = conn.cursor()
    try:
        _init_db_inner(conn, cur)
    except Exception as e:
        conn.rollback()
        print(f"[CRITICAL] Database initialization failed: {e}")
        raise
    finally:
        conn.close()


def _init_db_inner(conn, cur):

    # =========================
    # STUDENTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_no TEXT UNIQUE,
        full_name TEXT,
        gender TEXT,
        class TEXT,
        stream TEXT,
        level TEXT
    )
    """)
    
        # =========================
        # # =========================
    # TEACHERS
    # =========================
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_no TEXT UNIQUE,
        full_name TEXT NOT NULL,
        gender TEXT,
        phone TEXT,
        email TEXT,
        status TEXT DEFAULT 'ACTIVE',
        level TEXT
    )
    """)
    
    # =========================
    # TEACHER SUBJECTS
    # =========================
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_subjects (
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
    )
    """)
    
    # =========================
    # TEACHER CLASSES
    # =========================
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teacher_classes (
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
)
""")

    # =========================
    # SUBJECTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT,
        subject_short_name TEXT,
        level TEXT,
        subject_type TEXT,
        UNIQUE(subject_name, level)
    )
    """)

    # =========================
    # ENROLLMENTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
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
    )
    """)

    # =========================
    # REQUIREMENTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requirements (
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
    )
    """)

  

    # =========================
    # ACADEMIC YEARS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS academic_years (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year_name TEXT UNIQUE,
        is_active INTEGER DEFAULT 0
    )
    """)

    # =========================
    # TERMS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term_name TEXT,
        academic_year_id INTEGER,
        is_active INTEGER DEFAULT 0,

        FOREIGN KEY (academic_year_id)
        REFERENCES academic_years(id)
        ON DELETE CASCADE
    )
    """)

    # =========================
    # EXAMS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_name TEXT,
        term_id INTEGER,
        level TEXT,
        status TEXT DEFAULT 'OPEN',

        FOREIGN KEY (term_id)
        REFERENCES terms(id)
        ON DELETE CASCADE
    )
    """)

    # =========================
    # RESULTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
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
    )
    """)

    # =========================
    # DIVISION RULES
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS division_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT,
        division TEXT,
        min_points INTEGER,
        max_points INTEGER,
        UNIQUE(level, division)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS grade_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL,
        grade TEXT NOT NULL,
        min_mark INTEGER NOT NULL,
        max_mark INTEGER NOT NULL,
        points INTEGER NOT NULL,
        sort_order INTEGER DEFAULT 0,
        UNIQUE(level, grade)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subject_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT UNIQUE,
        required_subjects INTEGER,
        best_of INTEGER,
        compulsory_passes INTEGER DEFAULT 0
    )
    """)

    cur.execute("SELECT COUNT(*) FROM subject_requirements")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO subject_requirements (
                level,
                required_subjects,
                best_of,
                compulsory_passes
            ) VALUES (?, ?, ?, ?)
        """, [
            ("O_LEVEL", 7, 7, 0),
            ("A_LEVEL", 3, 3, 0),
        ])

    conn.commit()

    # =========================
    # DEFAULT DATA
    # =========================

    cur.execute("SELECT COUNT(*) FROM academic_years")
    if cur.fetchone()[0] == 0:

        cur.execute("""
        INSERT INTO academic_years(year_name, is_active)
        VALUES ('2026', 1)
        """)

        year_id = cur.lastrowid

        cur.execute("""
        INSERT INTO terms(term_name, academic_year_id, is_active)
        VALUES ('Term I', ?, 1)
        """, (year_id,))

        term1 = cur.lastrowid

        cur.execute("""
        INSERT INTO terms(term_name, academic_year_id, is_active)
        VALUES ('Term II', ?, 0)
        """, (year_id,))

        term2 = cur.lastrowid

        # Default Exams
        defaults = [
            ("Midterm", term1),
            ("Terminal", term1),
            ("Midterm", term2),
            ("Annual", term2)
        ]

        for index, (exam_name, term_id) in enumerate(defaults):
            status = "OPEN" if index == 0 else "CLOSED"

            cur.execute("""
            INSERT INTO exams(
                exam_name,
                term_id,
                level,
                status
            )
            VALUES (?, ?, ?, ?)
            """, (
                exam_name,
                term_id,
                "O_LEVEL",
                status
            ))

            cur.execute("""
            INSERT INTO exams(
                exam_name,
                term_id,
                level,
                status
            )
            VALUES (?, ?, ?, ?)
            """, (
                exam_name,
                term_id,
                "A_LEVEL",
                status
            ))

    # Default Division Rules (Tanzania Standard Example)
    cur.execute("SELECT COUNT(*) FROM division_rules")
    if cur.fetchone()[0] == 0:
        rules = [
            # O-Level (Best 7)
            ("O_LEVEL", "I", 7, 17),
            ("O_LEVEL", "II", 18, 21),
            ("O_LEVEL", "III", 22, 25),
            ("O_LEVEL", "IV", 26, 33),
            ("O_LEVEL", "0", 34, 35),
            # A-Level (Best 3)
            ("A_LEVEL", "I", 3, 9),
            ("A_LEVEL", "II", 10, 12),
            ("A_LEVEL", "III", 13, 17),
            ("A_LEVEL", "IV", 18, 19),
            ("A_LEVEL", "0", 20, 21)
        ]

        cur.execute("SELECT COUNT(*) FROM grade_rules")

        if cur.fetchone()[0] == 0:

            grades = [
        
                ("O_LEVEL","A",75,100,1,1),
                ("O_LEVEL","B",65,74,2,2),
                ("O_LEVEL","C",45,64,3,3),
                ("O_LEVEL","D",30,44,4,4),
                ("O_LEVEL","F",0,29,5,5),
        
                ("A_LEVEL","A",80,100,1,1),
                ("A_LEVEL","B",70,79,2,2),
                ("A_LEVEL","C",60,69,3,3),
                ("A_LEVEL","D",50,59,4,4),
                ("A_LEVEL","E",40,49,5,5),
                ("A_LEVEL","S",35,39,6,6),
                ("A_LEVEL","F",0,34,7,7),
        
            ]
        
            cur.executemany("""
        
                INSERT INTO grade_rules
        
                (level,grade,min_mark,max_mark,points,sort_order)
        
                VALUES(?,?,?,?,?,?)
        
        """, grades)
        
            cur.executemany("""
                    INSERT INTO division_rules (level, division, min_points, max_points)
                    VALUES (?, ?, ?, ?)
        """,rules)

    # =========================
    # SYSTEM SETTINGS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT
    )
    """)

    # =========================
    # SCHOOL PROFILE
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS school_profile (
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
    )
    """)

    # =========================
    # SCHOOL PROFILE MIGRATION
    # =========================
    print("[DATABASE] Running School Profile migration check...")
    cur.execute("PRAGMA table_info(school_profile)")
    columns = [row[1] for row in cur.fetchall()]
    
    v5_columns = [
        ('school_motto', 'TEXT'), ('school_address', 'TEXT'), ('school_phone', 'TEXT'),
        ('school_email', 'TEXT'), ('school_website', 'TEXT'), ('head_teacher', 'TEXT'),
        ('academic_master', 'TEXT'), ('school_logo', 'TEXT'), ('school_stamp', 'TEXT'),
        ('login_background', 'TEXT'), ('dashboard_background', 'TEXT'),
        ('watermark_text', 'TEXT DEFAULT "CONFIDENTIAL"'), ('created_at', 'TEXT DEFAULT CURRENT_TIMESTAMP')
    ]

    legacy_map = {
        'motto': 'school_motto', 'address': 'school_address', 'phone': 'school_phone',
        'email': 'school_email', 'headmaster': 'head_teacher'
    }

    # 1. Ensure all new columns exist (validate identifiers to prevent SQL injection)
    for col, definition in v5_columns:
        if col not in columns:
            _validate_identifier(col)
            _validate_definition(definition)
            print(f"[MIGRATION] Adding missing column: {col}")
            cur.execute(f"ALTER TABLE school_profile ADD COLUMN {col} {definition}")

    # 2. Map legacy data if legacy columns exist (validate identifiers)
    for old_col, new_col in legacy_map.items():
        if old_col in columns:
            _validate_identifier(old_col)
            _validate_identifier(new_col)
            print(f"[MIGRATION] Moving legacy data: {old_col} -> {new_col}")
            cur.execute(f"UPDATE school_profile SET {new_col} = {old_col} WHERE {new_col} IS NULL OR {new_col} = ''")

    
    # =========================
    # SUBJECTS MIGRATION
    # =========================
    cur.execute("PRAGMA table_info(subjects)")
    subject_columns = [row[1] for row in cur.fetchall()]

    if "subject_short_name" not in subject_columns:
        print("[MIGRATION] Adding subject_short_name...")
        cur.execute("""
            ALTER TABLE subjects
            ADD COLUMN subject_short_name TEXT
        """)


    print("[DATABASE] School profile migration check complete.")

    # =========================
    # SYSTEM SECURITY
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_security (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_passcode TEXT,
        security_question_1 TEXT,
        security_answer_1 TEXT,
        security_question_2 TEXT,
        security_answer_2 TEXT,
        last_changed TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("PRAGMA table_info(system_security)")
    security_columns = [row[1] for row in cur.fetchall()]
    for col in ("admin_passcode", "security_question_1", "security_answer_1", "security_question_2", "security_answer_2"):
        if col not in security_columns:
            _validate_identifier(col)
            print(f"[MIGRATION] Adding missing security column: {col}")
            cur.execute(f"ALTER TABLE system_security ADD COLUMN {col} TEXT")

    def _hash_secret(value):
        salt = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            value.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=260000,
        )
        return f"{salt}${dk.hex()}"

    cur.execute("SELECT COUNT(*) FROM system_security")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT school_name, head_teacher FROM school_profile LIMIT 1")
        profile = cur.fetchone() or ("SRMS V5", "ADMIN")
        school_name = (profile[0] or "SRMS V5").strip()
        head_teacher = (profile[1] or "ADMIN").strip()

        cur.execute(
            """
            INSERT INTO system_security (
                admin_passcode,
                security_question_1,
                security_answer_1,
                security_question_2,
                security_answer_2
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                _hash_secret("000000"),
                "What is the school name?",
                _hash_secret(school_name),
                "What is the head teacher's name?",
                _hash_secret(head_teacher),
            )
        )
    else:
        cur.execute("""
            UPDATE system_security
            SET
                security_question_1 = COALESCE(NULLIF(security_question_1, ''), 'What is the school name?'),
                security_question_2 = COALESCE(NULLIF(security_question_2, ''), 'What is the head teacher''s name?')
            WHERE id = (SELECT id FROM system_security ORDER BY id DESC LIMIT 1)
        """)

        cur.execute("""
            SELECT id, admin_passcode, security_answer_1, security_answer_2
            FROM system_security
            ORDER BY id DESC
            LIMIT 1
        """)
        sec_row = cur.fetchone()
        if sec_row:
            sec_id, admin_passcode, answer1, answer2 = sec_row
            needs_passcode = not admin_passcode
            needs_answers = not answer1 or not answer2

            if needs_passcode or needs_answers:
                cur.execute("SELECT school_name, head_teacher FROM school_profile LIMIT 1")
                profile = cur.fetchone() or ("SRMS V5", "ADMIN")
                school_name = (profile[0] or "SRMS V5").strip()
                head_teacher = (profile[1] or "ADMIN").strip()

                cur.execute(
                    """
                    UPDATE system_security
                    SET
                        admin_passcode=COALESCE(NULLIF(admin_passcode, ''), ?),
                        security_answer_1=COALESCE(NULLIF(security_answer_1, ''), ?),
                        security_answer_2=COALESCE(NULLIF(security_answer_2, ''), ?)
                    WHERE id=?
                    """,
                    (
                        _hash_secret("000000"),
                        _hash_secret(school_name),
                        _hash_secret(head_teacher),
                        sec_id,
                    )
                )

    # Default Settings
    cur.execute("SELECT COUNT(*) FROM system_settings")
    if cur.fetchone()[0] == 0:
        defaults = [
            ('o_level_counted', '7'),
            ('a_level_principal', '3'),
            ('show_logo', '1'),
            ('show_watermark', '1'),
            ('show_gender_summary', '1'),
            ('show_subject_ranking', '1'),
            ('show_requirements', '1'),
            ('auto_promotion', '0'),
            ('confirm_promotion', '1'),
            ('theme', 'Blue'),
            ('default_level', 'O_LEVEL'),
            ('backup_folder', './backups'),
            ('auto_backup', '0'),
            ('schema_version', '2')  # Version 2 = migrated schema with new column names
        ]
        cur.executemany("INSERT INTO system_settings VALUES (?, ?)", defaults)
    
    # Ensure schema_version is set for existing databases
    cur.execute("SELECT COUNT(*) FROM system_settings WHERE setting_key='schema_version'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO system_settings (setting_key, setting_value) VALUES ('schema_version', '2')")

    # Preserve the newest open exam and close legacy duplicates per level.
    cur.execute("""
        UPDATE exams
        SET status='CLOSED'
        WHERE status='OPEN'
          AND id NOT IN (
              SELECT MAX(id)
              FROM exams
              WHERE status='OPEN'
              GROUP BY level
          )
    """)

    conn.commit()
