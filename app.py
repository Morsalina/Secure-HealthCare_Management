from flask import Flask, request  # type: ignore[reportMissingImports]
from flask import render_template  # type: ignore[reportMissingImports]
from datetime import date
import re
from werkzeug.security import generate_password_hash, check_password_hash
from sqlite3 import IntegrityError
import sqlite3
from database import get_db_connection

app = Flask(__name__)

@app.route('/')
def welcomePage():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        errors={}

        if not email:
            errors['email'] = 'Required'
        else:
            email_pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
            if not re.match(email_pattern, email):
                errors['email'] = 'Invalid email address'

        if not password:
            errors['password'] = 'Required'

        if errors:
            return render_template(
                'login.html',
                errors=errors,
                email=email,
            )

        connection = get_db_connection()

        try:
            user = connection.execute("""
                SELECT
                    user_id,
                    email,
                    password_hash,
                    role,
                    account_status,
                    email_verified
                FROM users
                WHERE email = ?
            """, (email,)).fetchone()

        finally:
            connection.close()

        if user is None:
            errors['email'] = 'Invalid email or password.'

            return render_template(
                'login.html',
                errors=errors
            )

        if not check_password_hash(user['password_hash'], password):
            errors['email'] = 'Invalid email or password.'

            return render_template(
                'login.html',
                errors=errors
            )

        if user['account_status'] != 'active':
            errors['email'] = 'Your account is not active.'

            return render_template(
                'login.html',
                errors=errors
            )

        if user['email_verified'] != 1:
            errors['email'] = 'Please verify your email before logging in.'

            return render_template(
                'login.html',
                errors=errors
            )

        return "Credentials verified successfully!"

    return render_template('login.html', errors={})

@app.route('/register', methods=['GET', 'POST'])
def registerPage():

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        dob = request.form.get('dob', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Store errors for individual fields
        errors = {}

        if not first_name:
            errors['first_name'] = 'Required'

        if not last_name:
            errors['last_name'] = 'Required'

        if not email:
            errors['email'] = 'Required'
        else:
            email_pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
            if not re.match(email_pattern, email):
                errors['email'] = 'Invalid email address'

        if not dob:
            errors['dob'] = 'Required'
        else:
            try:
                birth_date = date.fromisoformat(dob)
                if birth_date > date.today():
                    errors['dob'] = 'Date of Birth can not be future date'

            except ValueError:
                errors['dob'] = 'Invalid date'

        if not password:
            errors['password'] = 'Required'
        elif len(password) < 12:
            errors['password'] = 'Password must contain at least 12 characters'

        if not confirm_password:
            errors['confirm_password'] = 'Required'
        elif password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        if errors:
            return render_template(
                'register.html',
                errors=errors,
                first_name=first_name,
                last_name=last_name,
                email=email,
                dob=dob
            )

        connection = get_db_connection()
        try:
            cursor = connection.execute("""
                INSERT INTO users (
                    first_name,
                    last_name,
                    email,
                    password_hash,
                    role,
                    account_status,
                    email_verified
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                first_name,
                last_name,
                email,
                generate_password_hash(password),
                'patient',   ##only patients can register, so the default role is patient
                'pending',
                0
            ))

            user_id = cursor.lastrowid

            connection.execute("""
                INSERT INTO patients (
                    user_id,
                    date_of_birth
                )
                VALUES (?, ?)
            """, (user_id, dob))

            connection.commit()

            return "Patient registration successful! Email verification is still pending."

        except IntegrityError:
            connection.rollback()

            errors['email'] = 'This email address is already registered.'

            return render_template(
                'register.html',
                errors=errors,
                first_name=first_name,
                last_name=last_name,
                email=email,
                dob=dob
            )

        finally:
            connection.close()


    return render_template('register.html', errors={})

if __name__ == '__main__':
    app.run(debug = True)

