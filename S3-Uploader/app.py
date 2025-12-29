import os
from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

S3_BUCKET = os.getenv('S3_BUCKET_NAME')
S3_KEY = os.getenv('AWS_ACCESS_KEY_ID')
S3_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')
S3_REGION = os.getenv('S3_REGION')

s3_client = boto3.client(
    's3',
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET,
    region_name=S3_REGION
)

@app.route('/')
def index():
    files_data = []
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        
        if 'Contents' in response:
            for item in response['Contents']:
                file_key = item['Key']
                
                # NEW: Generate a temporary URL for this file
                # 'ExpiresIn=3600' means the link works for 1 hour (3600 seconds)
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': file_key},
                    ExpiresIn=3600
                )
                
                # Add the name and the URL to our list
                files_data.append({'key': file_key, 'url': presigned_url})
            
    except Exception as e:
        flash(f"Error getting file list: {str(e)}")

    return render_template('index.html', files=files_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        try:
            s3_client.upload_fileobj(file, S3_BUCKET, file.filename)
            flash(f'File {file.filename} uploaded successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error uploading file: {str(e)}')
            return redirect(request.url)

# NEW: Route to handle deletion
@app.route('/delete', methods=['POST'])
def delete_file():
    key = request.form.get('key')  # Get filename from the form
    
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        flash(f'File {key} deleted successfully!')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}')
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    #app.run(debug=True, port=5000)
    #app.run(host='0.0.0.0', port=5000, debug=True)
    # Add ssl_context with your cert and key
    #app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=('cert.pem', 'key.pem'))if __name__ == '__main__':
    # Add threaded=True to handle multiple connections at once
    #app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=('cert.pem', 'key.pem'), threaded=True)
    # Ensure you are using '0.0.0.0'
    # threaded=True is important so it doesn't freeze
    #context = ('cert.pem', 'key.pem') 
    #app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=context, threaded=True)
    #if __name__ == '__main__':
    # IMPORTANT: set debug=False
    app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=('cert.pem', 'key.pem'))
