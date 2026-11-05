import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "instance" / "securecare.db"


def get_db_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_users_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL COLLATE NOCASE UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (
                role IN ('patient', 'care_worker', 'admin')
            ),
            account_status TEXT NOT NULL DEFAULT 'pending' CHECK (
                account_status IN ('pending', 'active', 'disabled')
            ),
            email_verified INTEGER NOT NULL DEFAULT 0 CHECK (
                email_verified IN (0, 1)
            ),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def create_patients_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            date_of_birth TEXT NOT NULL,
            phone TEXT,
            address TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


def create_care_workers_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS care_workers (
            worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            employee_id TEXT NOT NULL UNIQUE,
            qualification TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


def create_care_worker_assignments_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS care_worker_assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'inactive')),

            FOREIGN KEY (patient_id)
                REFERENCES patients(patient_id),

            FOREIGN KEY (worker_id)
                REFERENCES care_workers(worker_id)
        )
    """)

    connection.commit()
    connection.close()




def create_patient_records_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS patient_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            created_by_user_id INTEGER NOT NULL,
            updated_by_user_id INTEGER,
            record_type TEXT NOT NULL,
            record_content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,

            FOREIGN KEY (patient_id)
                REFERENCES patients(patient_id),

            FOREIGN KEY (created_by_user_id)
                REFERENCES users(user_id),

            FOREIGN KEY (updated_by_user_id)
                REFERENCES users(user_id)
        )
    """)

    connection.commit()
    connection.close()



def create_notifications_table():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0
                CHECK (is_read IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
        )
    """)

    connection.commit()
    connection.close()



def create_audit_logs_table():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            record_type TEXT,
            record_id INTEGER,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (actor_user_id)
                REFERENCES users(user_id),

            FOREIGN KEY (patient_id)
                REFERENCES patients(patient_id)
        )
    """)

    connection.commit()
    connection.close()



def create_email_verifications_table():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            verification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            otp_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_used INTEGER NOT NULL DEFAULT 0
                CHECK (is_used IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
        )
    """)

    connection.commit()
    connection.close()

## to prevent duplicate worker-patient assignment
def create_database_indexes():
    connection = get_db_connection()

    connection.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        unique_active_patient_worker
        ON care_worker_assignments (patient_id, worker_id)
        WHERE status = 'active'
    """)

    connection.commit()
    connection.close()



## initialize the database

def initialize_database():
    create_users_table()
    create_patients_table()
    create_care_workers_table()
    create_care_worker_assignments_table()
    create_patient_records_table()
    create_notifications_table()
    create_audit_logs_table()
    create_email_verifications_table()
    create_database_indexes()

    print("SecureCare database initialized successfully!")



## TO check if the tables are actually created
def check_tables():
    connection = get_db_connection()

    tables = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """).fetchall()

    for table in tables:
        print(table["name"])

    connection.close()

def view_registered_users():
    connection = get_db_connection()

    users = connection.execute("""
        SELECT
            user_id,
            first_name,
            last_name,
            email,
            role,
            password_hash,
            account_status,
            email_verified,
            created_at
        FROM users
    """).fetchall()

    for user in users:
        print(dict(user))

    connection.close()


def view_patient_profiles():
    connection = get_db_connection()

    patients = connection.execute("""
        SELECT
            patient_id,
            user_id,
            date_of_birth,
            phone,
            address
        FROM patients
    """).fetchall()

    for patient in patients:
        print(dict(patient))

    connection.close()

if __name__ == "__main__":
   # initialize_database()
    check_tables() #for printing the tables
    view_registered_users()
    view_patient_profiles()