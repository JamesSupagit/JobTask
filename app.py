from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workload.db'
db = SQLAlchemy(app)

# Create a model for storing workloads
class Workload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    morning_task = db.Column(db.String(200), nullable=False)
    afternoon_task = db.Column(db.String(200), nullable=False)

# Route for displaying the form
@app.route('/')
def index():
    return render_template('index.html')

# Route for submitting the form data
@app.route('/submit', methods=['POST'])
def submit_task():
    name = request.form['name']
    morning_task = request.form['morning_task']
    afternoon_task = request.form['afternoon_task']

    # Store workload in the database
    new_workload = Workload(name=name, morning_task=morning_task, afternoon_task=afternoon_task)
    db.session.add(new_workload)
    db.session.commit()

    return 'Job details submitted!'

# Function to send daily workloads to LINE
def send_daily_report():
    all_workloads = Workload.query.all()
    workload_summary = "Daily Job Workload:\n"
    
    for workload in all_workloads:
        workload_summary += f"Name: {workload.name}\nMorning Task: {workload.morning_task}\nAfternoon Task: {workload.afternoon_task}\n\n"

    # Send the workload summary to LINE
    line_notify_token = os.getenv('LINE_NOTIFY_TOKEN')
    line_notify_url = 'https://notify-api.line.me/api/notify'
    headers = {
        'Authorization': f'Bearer {line_notify_token}'
    }
    data = {
        'message': workload_summary
    }
    requests.post(line_notify_url, headers=headers, data=data)

# Schedule the job to send workload report at 17:30 GMT+7 every day
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_report, 'cron', hour=17, minute=30, timezone='Asia/Bangkok')
scheduler.start()

# Ensure that the scheduler is shut down when the app exits
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    scheduler.shutdown()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database if it doesn't exist
    app.run(debug=True, host='0.0.0.0')
