from flask import Flask, request, render_template_string
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

app = Flask(__name__)

# Define the LINE Notify token (replace with your own token)
LINE_NOTIFY_TOKEN = 'ymRbTJP3GwNeaFd3K6KI37Budn8026qOuiKzTbqswL0'  # Replace with your actual token

# Define the HTML template for the form
form_template = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Workload Tracker</title>
</head>
<body>
    <h1>Enter Workload Information</h1>
    <form action="/submit" method="post">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required><br><br>
        <label for="workload">Workload:</label>
        <textarea id="workload" name="workload" rows="10" cols="50" required></textarea><br><br>
        <input type="submit" value="Submit">
    </form>
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
        print(f'Sent to LINE: {response.status_code}, {response.text}')  # Debugging line
    except Exception as e:
        print(f'Error sending LINE notification: {e}')

@app.route('/')
def index():
    return render_template_string(form_template)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    workload = request.form['workload']
    message = f"Name: *{name}*\nWorkload: {workload}"
    # Format the latest workload message
    return_message = f"<h2>Latest Workload Submission</h2><p><strong>Name:</strong> {name}</p><p><strong>Workload:</strong><br>{workload.replace('\n', '<br>')}</p>"
    # Store the workload data
    workload_data.append(message)
    # Print workload data for debugging
    print(message)
    # Return a response with the confirmation and the latest workload message in HTML format
    return f"<html><body><h1>Data received!</h1><p>Here's the latest workload:</p>{return_message}<p>We will notify you at 17:30 GMT+7.</p></body></html>"

def job():
    # Send a separate message for each workload entry
    for workload in workload_data:
        send_line_notify(workload)
    # Clear the workload data after sending
    workload_data.clear()

# Schedule the job at 17:30 GMT+7 every day
def schedule_job():
    tz = pytz.timezone('Asia/Bangkok')
    scheduler.add_job(job, 'cron', hour=11, minute=38, timezone=tz)

# Start the scheduler
scheduler.start()
schedule_job()

if __name__ == '__main__':
    app.run(debug=True)
