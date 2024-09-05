from flask import Flask, request, render_template_string, render_template
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

app = Flask(__name__)

# Define the LINE Notify token (replace with your own token)
LINE_NOTIFY_TOKEN = 'ymRbTJP3GwNeaFd3K6KI37Budn8026qOuiKzTbqswL0'  # Replace with your actual token

# Define the HTML template for the form with improved styling
form_template = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workload Tracker</title>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Enter Workload Information</h1>
        <form action="/submit" method="post">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" required>
            <label for="workload">Workload:</label>
            <textarea id="workload" name="workload" rows="10" required></textarea>
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
        print(f'Sent to LINE: {response.status_code}, {response.text}')  # Debugging line
    except Exception as e:
        print(f'Error sending LINE notification: {e}')

@app.route('/')
def index():
    return render_template_string(form_template)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    workload = request.form.get('workload')

    # Replace newlines with HTML <br> tags for proper display
    formatted_workload = workload.replace('\n', '<br>')

    # Debugging output
    print(f"Received name: {name}")
    print(f"Received workload: {workload}")

    # Render the HTML template with the data
    return render_template('response.html', name=name, workload=formatted_workload)





def job():
    # Send a separate message for each workload entry
    for workload in workload_data:
        send_line_notify(workload)
    # Clear the workload data after sending
    workload_data.clear()

# Schedule the job at 17:30 GMT+7 every day
def schedule_job():
    tz = pytz.timezone('Asia/Bangkok')
    scheduler.add_job(job, 'cron', hour=13, minute=22, timezone=tz)

# Start the scheduler
scheduler.start()
schedule_job()

if __name__ == '__main__':
    # Run the Flask app on port 80
    app.run(host='0.0.0.0', port=80)
