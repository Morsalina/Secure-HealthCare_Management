
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
