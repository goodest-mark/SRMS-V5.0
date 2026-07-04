import sqlite3

from ui.pages.initial_setup_wizard import needs_initial_setup


def test_needs_initial_setup_when_school_profile_missing(initialized_db):
    assert needs_initial_setup() is True


def test_needs_initial_setup_false_after_profile_completed(initialized_db):
    conn = sqlite3.connect(initialized_db)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO school_profile (
            school_name, school_motto, school_address, school_phone,
            school_email, school_website, head_teacher, academic_master,
            discipline_master, class_master, school_logo, school_stamp,
            head_teacher_signature, academic_master_signature,
            discipline_master_signature, class_master_signature,
            login_background, dashboard_background, watermark_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Test School", "", "", "", "", "", "", "", "", "", "", "",
            "", "", "", "", "", "", "CONFIDENTIAL",
        ),
    )
    cur.execute(
        "REPLACE INTO system_settings (setting_key, setting_value) VALUES ('setup_complete', '1')"
    )
    conn.commit()
    conn.close()

    assert needs_initial_setup() is False
