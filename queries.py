
from database import get_db_connection
from werkzeug.security import generate_password_hash
from mysql.connector import IntegrityError


def register_patient(first_name, last_name, email, dob, password):

    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        # 1. Insert the user account
        cursor.execute("""
            INSERT INTO users (
                first_name,
                last_name,
                email,
                password_hash,
                user_roles,
                account_status,
                email_verified
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            first_name,
            last_name,
            email,
            generate_password_hash(password),
            'patient',
            'pending',
            0
        ))

        # 2. Retrieve the automatically generated user ID
        user_id = cursor.lastrowid

        # 3. Insert the corresponding patient profile
        cursor.execute("""
            INSERT INTO patients (
                user_id,
                date_of_birth
            )
            VALUES (%s, %s)
        """, (user_id, dob))

        # 4. Save both inserts together
        connection.commit()

        return "success"

    except IntegrityError as error:

        connection.rollback()

        # Error 1062 indicates a duplicate entry
        if error.errno == 1062:
            return "duplicate_email"

        raise

    except Exception:
        connection.rollback()
        raise

    finally:

        if cursor:
            cursor.close()

        connection.close()


def get_user_by_email(email):

    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                user_id,
                first_name,
                last_name,
                email,
                password_hash,
                user_roles,
                account_status,
                email_verified
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        return user

    finally:

        if cursor:
            cursor.close()

        connection.close()


def get_user_by_id(user_id):

    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                user_id,
                first_name,
                last_name,
                email,
                user_roles,
                account_status,
                email_verified
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        user = cursor.fetchone()

        return user

    finally:

        if cursor:
            cursor.close()

        connection.close()

def get_all_user():
    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
                    SELECT
                        user_id,
                        first_name,
                        last_name,
                        email,
                        user_roles,
                        account_status,
                        email_verified
                    FROM users
                """)
        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        connection.close()



def get_admin_patients():
    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                p.patient_id,
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                p.date_of_birth,
                p.phone,
                p.address,
                u.account_status,
                u.email_verified
            FROM patients p
            JOIN users u ON p.user_id = u.user_id
            ORDER BY p.patient_id DESC
        """)
        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_admin_care_workers():
    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                cw.worker_id,
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                cw.employee_id,
                cw.qualification,
                u.account_status,
                u.email_verified
            FROM care_workers cw
            JOIN users u ON cw.user_id = u.user_id
            ORDER BY cw.worker_id DESC
        """)
        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_admin_assignments():
    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                a.assignment_id,
                a.patient_id,
                a.worker_id,
                a.assigned_at,
                a.assignment_status,

                pu.first_name AS patient_first_name,
                pu.last_name AS patient_last_name,

                wu.first_name AS worker_first_name,
                wu.last_name AS worker_last_name,

                cw.employee_id

            FROM care_worker_assignments a

            JOIN patients p
                ON a.patient_id = p.patient_id

            JOIN users pu
                ON p.user_id = pu.user_id

            JOIN care_workers cw
                ON a.worker_id = cw.worker_id

            JOIN users wu
                ON cw.user_id = wu.user_id

            ORDER BY a.assignment_id DESC
        """)
        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        connection.close()


def get_admin_users():
    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                user_id,
                first_name,
                last_name,
                email,
                user_roles,
                account_status,
                email_verified,
                created_at
            FROM users
            ORDER BY user_id DESC
        """)
        return cursor.fetchall()

    finally:
        if cursor:
            cursor.close()
        connection.close()
