from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file
import boto3
from botocore.exceptions import ClientError
import requests
import io  # ספריה לניהול קבצים בזיכרון

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_john_bryce_labs'

# --- CONFIGURATION ---
ACCESS_KEY = 'ASIAYDP7HZX2DFRNQ5PQ'
SECRET_KEY = 'xxxxxxxxxxxxxxxxx'
SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEBIaCWV1LXdlc3QtMSJHMEUCIFabQd66Um92cDjxWAi+vfg9Xgbk68p3dz60Eb5gns+1AiEAqGq60aAd1tXf8qqOLghlYdOLP3iQNXgvGdDX4OqjwrwqrQII2///////////ARAAGgw1NTcyNzA0MjA5ODAiDJ4UHRbEkuUtWLq2JyqBAua4CBFK4/FpEpZ+vQg20vifHcQTtK2nOvsGF5crkWrHQcIkLrvNSgKaxOLQN7oXc6S4aQjgKInVu+cz1FJvyIHrxrYlIoo5ACCcCp30jtR05JvzSQVSwNcpgIWXF/G0IZmaBOvWm0wZ7zVFYDCVu8wiTKfVNqKVz9qaev2H/iCwgELLKsHd4DB7tM+E/Tt0RFEURLqXUT+zSY8QJxYNU63U4cgU2C+76nleRMiRNLpyIa7uZ0ZRAWtKKw12Ak/8DUywi7PbhlKT///EfCuHcOzIMi0q2p1asdTCtJfQ2lS7lsxelMfDpqP3BR2sCsXCwadyylsRZuQi32GHdD0vNMATMJ+8j8sGOp0B1BSbY8IlvKsZuTJi3g52OhzEd7iHTzmYCjoHsG6Hx0+otkqdrnwDIAp1hboaoIkktQ1RHAvDJ4kJtF33yej/uDo6o8ZoviGbtHuaymkvRfsT6Xae21h+irjqfRX0QZAiL4DOQTT2dqcXXHCI1yhNMEBOML27qvQJfYW54it4hKJGabaex1iMIFDsUL7ZZWz2HObgmxdx7Tv4uRXg+w=='
REGION = 'eu-west-1'
BUCKET_NAME = 'jblabs-moshe-bucket-upload'

# S3 Client
s3_client = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN,
    region_name=REGION
)

def get_ec2_ip():
    try:
        token = requests.put('http://169.254.169.254/latest/api/token', headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}, timeout=1).text
        ip = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', headers={'X-aws-ec2-metadata-token': token}, timeout=1).text
        return ip
    except:
        return "Localhost (Dev Mode)"

# --- HTML TEMPLATE ---
PRO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AWS S3 Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #f4f6f9; }
        .main-container { max-width: 900px; margin-top: 50px; }
        .server-badge { background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.9em; }
    </style>
</head>
<body>

<div class="container main-container">
    
    <div class="text-center mb-4">
        <h1 class="header-title"><i class="fab fa-aws"></i> S3 Cloud Manager</h1>
        <p class="text-muted">Server IP: <span class="server-badge">{{ ip_address }}</span></p>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }} alert-dismissible fade show">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="card shadow-sm mb-4">
        <div class="card-header bg-white">
            <h5 class="mb-0"><i class="fas fa-cloud-upload-alt"></i> Upload New File</h5>
        </div>
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data" class="row g-3 align-items-center">
                <div class="col-auto flex-grow-1">
                    <input type="file" class="form-control" name="file" required>
                </div>
                <div class="col-auto">
                    <button type="submit" name="action" value="upload" class="btn btn-success">
                        <i class="fas fa-arrow-up"></i> Upload
                    </button>
                </div>
            </form>
        </div>
    </div>

    <div class="card shadow-sm">
        <div class="card-header bg-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0"><i class="fas fa-folder-open"></i> Bucket Contents</h5>
            <span class="badge bg-secondary">{{ files|length }} Files</span>
        </div>
        <div class="card-body p-0">
            <table class="table table-hover table-striped mb-0">
                <thead class="table-light">
                    <tr>
                        <th>File Name</th>
                        <th>Size</th>
                        <th class="text-end">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for file in files %}
                    <tr>
                        <td class="align-middle"><i class="far fa-file-alt me-2 text-secondary"></i> {{ file['Key'] }}</td>
                        <td class="align-middle">{{ file['Size'] }} bytes</td>
                        <td class="text-end">
                            <a href="{{ url_for('download_file', key=file['Key']) }}" class="btn btn-outline-primary btn-sm me-1">
                                <i class="fas fa-download"></i> Download
                            </a>
                            
                            <form method="POST" style="display:inline;">
                                <input type="hidden" name="key" value="{{ file['Key'] }}">
                                <button type="submit" name="action" value="delete" class="btn btn-outline-danger btn-sm" onclick="return confirm('Delete this file?');">
                                    <i class="fas fa-trash-alt"></i> Delete
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="3" class="text-center py-4">Bucket is empty.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/health')
def health_check():
    # מחזיר תשובה ריקה או טקסט קצר וקוד 200
    return "OK", 200

# --- NEW REDIRECT ROUTE ---
@app.route('/assets')
def assets_redirect():
    # מפנה את המשתמש מהנתיב /assets חזרה לדף הראשי
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload':
            if 'file' not in request.files: return redirect(request.url)
            file = request.files['file']
            if file.filename == '': return redirect(request.url)
            try:
                s3_client.upload_fileobj(file, BUCKET_NAME, file.filename)
                flash(f'File "{file.filename}" uploaded!', 'success')
            except ClientError as e:
                flash(f'Error: {e}', 'danger')

        elif action == 'delete':
            key = request.form.get('key')
            try:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
                flash(f'Deleted "{key}"', 'info')
            except ClientError as e:
                flash(f'Error: {e}', 'danger')
        
        return redirect(url_for('index'))

    # List Files
    files = []
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in response:
            files = response['Contents']
    except ClientError as e:
        flash(f"Connection Error: {e}", 'danger')

    return render_template_string(PRO_HTML, bucket=BUCKET_NAME, files=files, ip_address=get_ec2_ip())

# --- NEW DOWNLOAD ROUTE ---
@app.route('/download')
def download_file():
    key = request.args.get('key')
    try:
        # 1. קריאת הקובץ מ-S3 לזיכרון של ה-EC2
        file_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        
        # 2. שליחת הקובץ לדפדפן כ-Attachment
        return send_file(
            io.BytesIO(file_obj['Body'].read()),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=key
        )
    except ClientError as e:
        flash(f"Error downloading: {e}", 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
