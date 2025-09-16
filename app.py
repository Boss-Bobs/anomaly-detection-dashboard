from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import os
import cv2
import numpy as np
import base64
import time
import json
from threading import Thread

# --- Flask App and WebSocket Setup ---
app = Flask(__name__)
# The secret key is needed for SocketIO
app.config['SECRET_KEY'] = 'your-very-secure-secret-key-that-should-be-kept-secret'
# Use gevent for efficient I/O handling in WebSockets
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

# --- Directory and Model Configuration (Mock) ---
# Assuming video is in the same directory as this script
VIDEO_PATH = "Anomaly-Videos/RoadAccidents046_x264.mp4"
ANOMALY_THRESHOLD = 0.5

# Mock data for demonstration purposes
MOCK_IMAGES_PATH = "static/images/anomaly_frames"
MOCK_TX_LOGS = [] # This would be populated from a real blockchain
last_known_frame = -1
last_known_error = 0.0

# --- Video Streaming and Anomaly Detection Thread ---
def video_stream_thread():
    """
    Simulates a live video stream, processes frames, and sends them
    over a WebSocket.
    """
    print("Starting video stream thread...")
    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print(f"Error: Could not open video file at {VIDEO_PATH}")
        return

    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # Loop the video if it ends
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # --- Mock Anomaly Detection Logic ---
            # In a real-world scenario, you would pass the frame through your
            # 3D convolutional autoencoder model here.
            # For demonstration, we'll create a simple mock anomaly score.
            # Anomaly is "detected" every 50 frames
            is_anomaly = (frame_count % 50 == 0 and frame_count > 0)
            anomaly_score = np.random.uniform(0.3, 0.9) if is_anomaly else np.random.uniform(0.1, 0.4)

            if is_anomaly:
                # Simulate a blockchain transaction log
                global last_known_frame, last_known_error
                last_known_frame = frame_count
                last_known_error = anomaly_score
                log = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "folder": "Mock_Anomaly",
                    "frame": last_known_frame,
                    "error": f"Error: {last_known_error:.4f}",
                }
                MOCK_TX_LOGS.append(log)

            # Encode the frame to a base64 string
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            # Prepare the data packet
            data = {
                "frame": frame_base64,
                "is_anomaly": is_anomaly,
                "anomaly_score": float(anomaly_score)
            }

            # Emit the data over the WebSocket
            socketio.emit('video_frame', json.dumps(data))

            frame_count += 1
            time.sleep(0.05) # Simulate a delay for a stable stream

    except Exception as e:
        print(f"Error in video stream thread: {e}")
    finally:
        cap.release()
        print("Video stream thread stopped.")

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/anomaly-images')
def get_anomaly_images():
    # Mocks the loading of anomaly images from a directory
    image_files = os.listdir(MOCK_IMAGES_PATH)
    images = []
    
    for filename in image_files:
        filepath = os.path.join(MOCK_IMAGES_PATH, filename)
        file_size = os.path.getsize(filepath)
        
        # Check if this image has a blockchain match
        blockchain_match = any(str(last_known_frame) in tx['frame'] for tx in MOCK_TX_LOGS)
        tx_data = {}
        if blockchain_match:
            tx_data = next((tx for tx in MOCK_TX_LOGS if str(last_known_frame) in tx['frame']), {})
            
        images.append({
            "filename": filename,
            "size": file_size,
            "blockchain_match": blockchain_match,
            "tx_data": tx_data
        })
        
    return jsonify({
        "success": True,
        "images": images,
        "total_count": len(images)
    })

@app.route('/api/image/<filename>')
def get_image(filename):
    filepath = os.path.join(MOCK_IMAGES_PATH, filename)
    if not os.path.exists(filepath):
        return jsonify({"success": False, "error": "Image not found"}), 404
    
    with open(filepath, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    return jsonify({"success": True, "image": f"data:image/jpeg;base64,{encoded_string}"})


@app.route('/api/blockchain-data')
def get_blockchain_data():
    # Mocks a real-time call to the blockchain
    if not MOCK_TX_LOGS:
        return jsonify({
            "success": True,
            "tx_logs": [],
            "anomaly_count": 0,
            "error": "No transactions found"
        })
    
    return jsonify({
        "success": True,
        "tx_logs": MOCK_TX_LOGS,
        "anomaly_count": len(MOCK_TX_LOGS),
        "last_frame": last_known_frame,
        "last_error": f"{last_known_error:.4f}"
    })

# --- WebSocket Event Handlers ---
@socketio.on('connect', namespace='/ws/video_feed')
def handle_connect():
    print('Client connected to video stream WebSocket')
    # Start the video stream thread when the first client connects
    thread = Thread(target=video_stream_thread)
    thread.start()

@socketio.on('disconnect', namespace='/ws/video_feed')
def handle_disconnect():
    print('Client disconnected from video stream WebSocket')

if __name__ == '__main__':
    # It's crucial to run with socketio.run() instead of app.run()
    # to enable the WebSocket functionality.
    print("Starting Flask-SocketIO server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
