from flask import (
    Flask, request, render_template,
    session, redirect, url_for, g
)
from flask import abort

from functools import wraps
from datetime import date, timedelta
import re
import os

from dotenv import load_dotenv
from werkzeug.security import check_password_hash

from queries import (
    register_patient,
    get_user_by_email,
    get_user_by_id,
    get_all_user,
    get_admin_patients,
    get_admin_care_workers,
    get_admin_assignments,
    get_admin_users
)

load_dotenv()


app = Flask(__name__)

##For configuring app sessions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY is missing from .env")

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.config['SESSION_COOKIE_SECURE'] = False #will be True when deployed over HTTS

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# implement a decorator
def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        user_id = session.get('user_id')

        if user_id is None:
            return redirect(url_for('login'))

        user = get_user_by_id(user_id)

        if user is None:
            session.clear()
            return redirect(url_for('login'))

        if user['account_status'] != 'active':
            session.clear()
            return redirect(url_for('login'))

        if user['email_verified'] != 1:
            session.clear()
            return redirect(url_for('login'))

        g.current_user = user

        return view(*args, **kwargs)

    return wrapped_view


# This function checks if the user has the authority/role to access a certain URL
def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):

            if g.current_user['user_roles'] not in allowed_roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped_view
    return decorator



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

        session.clear()
        session['user_id'] = user['user_id']
        session.permanent = True

        if user['user_roles'] == 'admin':
            return redirect(url_for('admin_dashboard'))

        elif user['user_roles'] == 'care_worker':
            return redirect(url_for('care_worker_dashboard'))

        else:
            return redirect(url_for('dashboard'))

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


@app.route('/dashboard')
@login_required
@role_required('patient')
def dashboard():

    return render_template(
        'dashboard.html',
        user=g.current_user
    )

@app.route('/care-worker')
@login_required
@role_required('care_worker')
def care_worker_dashboard():
    return "Care Worker Dashboard"



@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():

    selected_tab = request.args.get('tab', 'patients')

    # Only allow these four tab names.
    allowed_tabs = [
        'patients',
        'care_workers',
        'assignments',
        'users'
    ]

    if selected_tab not in allowed_tabs:
        abort(404)

    # Retrieve data for the selected tab.
    if selected_tab == 'patients':
        data = get_admin_patients()

    elif selected_tab == 'care_workers':
        data = get_admin_care_workers()

    elif selected_tab == 'assignments':
        data = get_admin_assignments()

    else:
        data = get_admin_users()

    return render_template(
        'admin_dashboard.html',
        user=g.current_user,
        selected_tab=selected_tab,
        data=data
    )


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
