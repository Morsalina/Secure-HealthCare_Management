
from flask import Flask, request, render_template
from datetime import date
import re

from werkzeug.security import check_password_hash

from queries import register_patient, get_user_by_email


app = Flask(__name__)


@app.route('/')
def welcomePage():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        errors = {}

        # Validate email
        if not email:
            errors['email'] = 'Required'
        else:
            email_pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

            if not re.match(email_pattern, email):
                errors['email'] = 'Invalid email address'

        # Validate password
        if not password:
            errors['password'] = 'Required'

        if errors:
            return render_template(
                'login.html',
                errors=errors,
                email=email
            )

        # Retrieve user from database
        user = get_user_by_email(email)

        # Check whether the account exists
        if user is None:
            errors['email'] = 'Invalid email or password.'

            return render_template(
                'login.html',
                errors=errors,
                email=email
            )

        # Verify submitted password against stored password hash
        if not check_password_hash(user['password_hash'], password):
            errors['email'] = 'Invalid email or password.'

            return render_template(
                'login.html',
                errors=errors,
                email=email
            )

        # Check account status
        if user['account_status'] != 'active':
            errors['email'] = 'Your account is not active.'

            return render_template(
                'login.html',
                errors=errors,
                email=email
            )

        # Check email verification
        if user['email_verified'] != 1:
            errors['email'] = 'Please verify your email before logging in.'

            return render_template(
                'login.html',
                errors=errors,
                email=email
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

        errors = {}

        # Validate first name
        if not first_name:
            errors['first_name'] = 'Required'

        # Validate last name
        if not last_name:
            errors['last_name'] = 'Required'

        # Validate email
        if not email:
            errors['email'] = 'Required'
        else:
            email_pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

            if not re.match(email_pattern, email):
                errors['email'] = 'Invalid email address'

        # Validate date of birth
        if not dob:
            errors['dob'] = 'Required'
        else:
            try:
                birth_date = date.fromisoformat(dob)

                if birth_date > date.today():
                    errors['dob'] = 'Date of Birth cannot be a future date'

            except ValueError:
                errors['dob'] = 'Invalid date'

        # Validate password
        if not password:
            errors['password'] = 'Required'
        elif len(password) < 12:
            errors['password'] = 'Password must contain at least 12 characters'

        # Validate password confirmation
        if not confirm_password:
            errors['confirm_password'] = 'Required'
        elif password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'

        # Return to registration page if validation fails
        if errors:
            return render_template(
                'register.html',
                errors=errors,
                first_name=first_name,
                last_name=last_name,
                email=email,
                dob=dob
            )

        # Register patient using the database function
        result = register_patient(
            first_name,
            last_name,
            email,
            dob,
            password
        )

        if result == "duplicate_email":

            errors['email'] = 'This email address is already registered.'

            return render_template(
                'register.html',
                errors=errors,
                first_name=first_name,
                last_name=last_name,
                email=email,
                dob=dob
            )

        return "Patient registration successful! Email verification is still pending."

    return render_template('register.html', errors={})


if __name__ == '__main__':
    app.run(debug=True)
