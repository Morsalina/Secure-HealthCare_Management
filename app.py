from flask import Flask, request  # type: ignore[reportMissingImports]
from flask import render_template  # type: ignore[reportMissingImports]
from datetime import date
import re

app = Flask(__name__)

@app.route('/')
def welcomePage():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

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

        return "Registration information passed validation!"

    return render_template('register.html', errors={})

if __name__ == '__main__':
    app.run(debug = True)

