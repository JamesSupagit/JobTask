from flask import Flask, request, render_template_string, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Dummy user store
users = {
    'admin': {'password': 'password123'}
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in users else None

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

# Define the LINE Notify token (replace with your own token)
LINE_NOTIFY_TOKEN = 'ymRbTJP3GwNeaFd3K6KI37Budn8026qOuiKzTbqswL0'  # Replace with your actual token

# Define the HTML template for the login form with improved styling and animation
login_template = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Workload SOC Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 0;
            overflow: hidden; /* Prevent scrolling to ensure the slideshow fits the viewport */
        }
        .login-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80%;
            max-width: 400px;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            z-index: 1; /* Ensure it's above the slideshow */
        }
        .login-container h1 {
            color: #007BFF;
            text-align: center;
            margin-bottom: 20px;
        }
        .login-container label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        .login-container input[type="text"], 
        .login-container input[type="password"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .login-container input[type="submit"] {
            background-color: #007BFF;
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        .login-container input[type="submit"]:hover {
            background-color: #0056b3;
        }
        .login-container .error {
            color: red;
            font-weight: bold;
        }
        .slideshow-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%; /* Full viewport height */
            overflow: hidden;
            z-index: 0;
        }
        .slide {
            position: absolute;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 1s ease-in-out;
        }
        .slide.active {
            opacity: 1;
        }
        .slide img {
            width: 100%;
            height: 100%;
            object-fit: cover; /* Ensures the image covers the container */
        }
    </style>
</head>
<body>
    <div class="slideshow-container">
        {% for i in range(1, 4) %}
            <div class="slide">
                <img src="{{ url_for('static', filename='cat' ~ i ~ '.jpg') }}" alt="Logo">
            </div>
        {% endfor %}
    </div>
    <div class="login-container">
        <h1>Login</h1>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required>
            <input type="submit" value="Login">
        </form>
    </div>
    <script>
        const slides = document.querySelectorAll('.slide');
        let currentSlide = 0;
        const slideInterval = 2000; // 2 seconds

        function showSlide(index) {
            slides.forEach((slide, i) => {
                slide.classList.toggle('active', i === index);
            });
        }

        function nextSlide() {
            currentSlide = (currentSlide + 1) % slides.length;
            showSlide(currentSlide);
        }

        setInterval(nextSlide, slideInterval);
        showSlide(currentSlide);
    </script>
</body>
</html>
'''

# Define the HTML template for the form with improved styling and character limit warning
form_template = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workload SOC Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 0;
        }
        h1 {
            color: #007BFF;
        }
        .container {
            width: 80%;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        input[type="submit"] {
            background-color: #007BFF;
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #0056b3;
        }
        .response {
            margin-top: 20px;
        }
        .warning {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Enter Workload Information</h1>
        {% if error %}
            <p class="warning">{{ error }}</p>
        {% endif %}
        <form action="/submit" method="post">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" required>
            <label for="workload">Workload (Max 1000 characters):</label>
            <textarea id="workload" name="workload" rows="10" maxlength="1000" required></textarea>
            <input type="submit" value="Submit">
        </form>
    </div>
</body>
</html>
'''

# Store workload data
workload_data = []

# Initialize the scheduler
scheduler = BackgroundScheduler()

def send_line_notify(message):
    headers = {
        'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}',
    }
    payload = {'message': message}
    try:
        response = requests.post('https://notify-api.line.me/api/notify', headers=headers, params=payload)
        print(f'Sent to LINE: {response.status_code}, {response.text}')
    except Exception as e:
        print(f'Error sending LINE notification: {e}')

@app.route('/')
@login_required
def index():
    error_message = request.args.get('error')
    return render_template_string(form_template, error=error_message)

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    name = request.form['name']
    workload = request.form['workload']

    if len(workload) > 1000:
        error_message = f"Error: Workload exceeds 1000 characters. You entered {len(workload)} characters."
        return redirect(url_for('index', error=error_message))

    timestamp = datetime.now().strftime('%d/%m/%Y')

    message = f"\nDate: {timestamp}\nName: *{name}*\nWorkload:\n {workload}\n"

    return_message = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 80%;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #007BFF;
                text-align: center;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
            }}
            .details {{
                margin: 20px 0;
                padding: 10px;
                background-color: #e9ecef;
                border-radius: 4px;
                box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
            }}
            .details h2 {{
                color: #007BFF;
                margin-top: 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Data Received!</h1>
            <p>Your workload information has been successfully submitted. Here's the latest entry:</p>
            <div class="details">
                <h2>Latest Workload Submission</h2>
                <p><strong>Date:</strong> {timestamp}</p>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Workload:</strong><br>{workload.replace('\n', '<br>')}</p>
            </div>
            <p>We will notify you at 17:30 GMT+7.</p>
        </div>
    </body>
    </html>
    """

    workload_data.append(message)
    print(message)
    return return_message

def job():
    for workload in workload_data:
        send_line_notify(workload)
    workload_data.clear()

def schedule_job():
    tz = pytz.timezone('Asia/Bangkok')
    scheduler.add_job(job, 'cron', hour=13, minute=35, timezone=tz)

scheduler.start()
schedule_job()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user['password'] == password:
            login_user(User(username))
            return redirect(url_for('index'))
        else:
            error_message = "Invalid username or password"
            return render_template_string(login_template, error=error_message)
    return render_template_string(login_template)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
