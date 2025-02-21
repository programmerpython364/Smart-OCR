import os
import uuid
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, Markup
from werkzeug.utils import secure_filename
from run import extract_image, extract_video, AI, initialize_llm

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this for production

# Set up an uploads folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions and size limits
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4'}
MAX_VIDEO_SIZE = 20 * 1024 * 1024  # 20 MB

# Global dictionaries for user sessions and video OCR data
user_sessions = {}  # key: user_id, value: dict with "chain", "memory", "chat_history"
video_data = {}     # key: video uid, value: dict with keys 'ocr_result' and 'file'

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def cleanup_user_session():
    """
    Remove all data associated with the current user's session.
    This includes removing any uploaded files, video data, and the AI memory.
    """
    user_id = session.get('user_id')
    if user_id and user_id in user_sessions:
        del user_sessions[user_id]
    for f in session.get('uploaded_files', []):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as err:
            print("Error deleting file:", file_path, err)
    video_uid = session.get('video_uid')
    if video_uid and video_uid in video_data:
        del video_data[video_uid]
    session.clear()

@app.before_request
def check_session_timeout():
    """
    Before every request, check if the session has been active for more than 30 minutes.
    If so, clean up all session data and redirect the user to the home page with a message.
    """
    if 'session_start' in session:
        try:
            session_start = datetime.strptime(session['session_start'], "%Y-%m-%d %H:%M:%S")
        except Exception:
            session_start = datetime.utcnow()
        if datetime.utcnow() - session_start > timedelta(minutes=30):
            cleanup_user_session()
            flash("Your session has expired due to inactivity. All data has been cleared.")
            return redirect(url_for('index'))

def get_user_session():
    """
    Retrieve or create a per-user session with a unique ID, chain, memory, and chat history.
    If the session has expired, it resets and starts fresh.
    """
    if 'session_start' not in session:
        session['session_start'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if 'user_id' not in session or session['user_id'] not in user_sessions:
        # If the user_id is missing or deleted, restart their session
        flash("Your session expired. A new session has been created.")
        session.clear()  # Ensure old session data is removed
        session['user_id'] = str(uuid.uuid4())  # Assign a new user_id
        chain, memory = initialize_llm()  # Create a fresh AI instance
        user_sessions[session['user_id']] = {
            "chain": chain,
            "memory": memory,
            "chat_history": []
        }

    return user_sessions[session['user_id']]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image', methods=['GET', 'POST'])
def image():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Track uploaded file for cleanup later
                session.setdefault('uploaded_files', []).append(filename)
                # Call the OCR function for images
                extracted_text = extract_image(filepath)
                return render_template('image.html', image_filename=filename, extracted_text=extracted_text)
            else:
                flash('Invalid file type for image')
                return redirect(request.url)
        return render_template('image.html')
    except Exception as e:
        raise Exception("Error in /image route: " + str(e))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/improve_text_image', methods=['POST'])
def improve_text_image():
    try:
        text = request.form.get('edited_text')
        if not text:
            flash('No text provided')
            return redirect(url_for('image'))
        
        # Try to get user session, handling expiration
        try:
            user_data = get_user_session()
        except KeyError:
            flash("Your session expired. Please restart.")
            return redirect(url_for('index'))  # Redirect to home page safely
        
        chain = user_data["chain"]
        memory = user_data["memory"]
        
        # Improve text using AI function
        improved_text = AI(text, chain, memory)
        
        # Initialize chat history
        user_data["chat_history"].append({"sender": "User", "message": text})
        user_data["chat_history"].append({"sender": "AI", "message": improved_text})
        
        return redirect(url_for('chat'))
    except Exception as e:
        raise Exception("Error in /improve_text_image route: " + str(e))

@app.route('/video', methods=['GET', 'POST'])
def video():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
                # Check video file size
                file.seek(0, os.SEEK_END)
                file_length = file.tell()
                file.seek(0)
                if file_length > MAX_VIDEO_SIZE:
                    flash('Video file exceeds 20 MB limit')
                    return redirect(request.url)
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                session.setdefault('uploaded_files', []).append(filename)
                flash('Processing video. This may take a while...')
                # Process the video to extract OCR for each frame
                ocr_result = extract_video(filepath)
                uid = str(uuid.uuid4())
                video_data[uid] = {'ocr_result': ocr_result, 'file': filename}
                session['video_uid'] = uid  # Associate this video with the user session
                total_frames = len(ocr_result)
                return redirect(url_for('select_frame', uid=uid, total_frames=total_frames))
            else:
                flash('Invalid file type for video')
                return redirect(request.url)
        return render_template('video.html')
    except Exception as e:
        raise Exception("Error in /video route: " + str(e))

@app.route('/select_frame/<uid>', methods=['GET', 'POST'])
def select_frame(uid):
    try:
        data = video_data.get(uid)
        if not data:
            flash('Video data not found')
            return redirect(url_for('video'))
        total_frames = len(data['ocr_result'])
        if request.method == 'POST':
            frame_number = request.form.get('frame_number')
            try:
                frame_number = int(frame_number)
            except ValueError:
                flash('Frame number must be an integer')
                return redirect(request.url)
            if frame_number < 0 or frame_number >= total_frames:
                flash(f'Frame number must be between 0 and {total_frames - 1}')
                return redirect(request.url)
            # Extract OCR result for the chosen frame
            frame_ocr = data['ocr_result'][frame_number]
            extracted_text = " ".join([text for (_, text, _) in frame_ocr])
            return render_template('video.html', uid=uid, total_frames=total_frames,
                                   selected_frame=frame_number, extracted_text=extracted_text,
                                   video_file=data['file'])
        return render_template('video.html', uid=uid, total_frames=total_frames, video_file=data['file'])
    except Exception as e:
        raise Exception("Error in /select_frame route: " + str(e))

@app.route('/improve_text_video/<uid>', methods=['POST'])
def improve_text_video(uid):
    try:
        text = request.form.get('edited_text')
        if not text:
            flash('No text provided')
            return redirect(url_for('select_frame', uid=uid))

        # Try to get user session, handling expiration
        try:
            user_data = get_user_session()
        except KeyError:
            flash("Your session expired. Please restart.")
            return redirect(url_for('index'))  # Redirect to home page safely

        chain = user_data["chain"]
        memory = user_data["memory"]
        
        # Improve text using AI function
        improved_text = AI(text, chain, memory)
        
        # Initialize chat history
        user_data["chat_history"].append({"sender": "User", "message": text})
        user_data["chat_history"].append({"sender": "AI", "message": improved_text})
        
        return redirect(url_for('chat'))
    except Exception as e:
        raise Exception("Error in /improve_text_video route: " + str(e))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    try:
        user_data = get_user_session()
        if request.method == 'POST':
            user_message = request.form.get('user_message')
            if not user_message:
                flash("Please enter a message.")
                return redirect(url_for('chat'))
            user_data["chat_history"].append({"sender": "User", "message": user_message})
            ai_response = AI(user_message, user_data["chain"], user_data["memory"])
            user_data["chat_history"].append({"sender": "AI", "message": ai_response})
            return redirect(url_for('chat'))
        return render_template('result.html', chat_history=user_data["chat_history"])
    except Exception as e:
        raise Exception("Error in /chat route: " + str(e))

@app.route('/logout')
def logout():
    try:
        user_id = session.get('user_id')
        session.clear()
        if user_id in user_sessions:
            del user_sessions[user_id]
        flash("Logged out successfully.")
        return redirect(url_for('index'))
    except Exception as e:
        raise Exception("Error in /logout route: " + str(e))

@app.errorhandler(Exception)
def handle_exception(e):
    # Get the full traceback for detailed error reporting
    tb = traceback.format_exc()
    error_details = Markup(f"""
    <html>
      <head>
        <title>Error Report</title>
        <style>
          body {{
            background: #f8d7da;
            font-family: Arial, sans-serif;
            color: #721c24;
            padding: 20px;
          }}
          .container {{
            background: #f5c6cb;
            border: 1px solid #f5c2c7;
            border-radius: 5px;
            padding: 20px;
            margin: auto;
            max-width: 800px;
          }}
          pre {{
            background: #f1f1f1;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
          }}
          a {{
            color: #721c24;
            text-decoration: underline;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Detailed Error Report</h1>
          <p><strong>Error Type:</strong> {type(e).__name__}</p>
          <p><strong>Error Message:</strong> {str(e)}</p>
          <h2>Traceback:</h2>
          <pre>{tb}</pre>
          <a href="{url_for('index')}">Back to Home</a>
        </div>
      </body>
    </html>
    """)
    return error_details, 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)