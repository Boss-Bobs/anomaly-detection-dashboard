import os
import base64
import json
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app
from blockchain import BlockchainService
import time
from threading import Lock

# Initialize blockchain service
blockchain_service = BlockchainService()

# Configuration for anomaly results directory (like Kaggle output)
ANOMALY_RESULTS_DIR = "anomaly_results/annotated_anomalies"

# Caching system
cache_lock = Lock()
blockchain_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 300  # 5 minutes cache
}
image_cache = {}

def image_to_base64(filepath):
    """Converts an image file to a Base64 encoded string."""
    try:
        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # Determine image type from file extension
        ext = filepath.rsplit('.', 1)[1].lower()
        if ext == 'png':
            return f"data:image/png;base64,{encoded_string}"
        else:
            return f"data:image/jpeg;base64,{encoded_string}"
    except FileNotFoundError:
        return ""

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/api/image/<filename>')
def get_single_image(filename):
    """API endpoint to get a single image on demand."""
    try:
        # Check cache first
        if filename in image_cache:
            app.logger.info(f"Serving {filename} from cache")
            return jsonify({
                'success': True,
                'image': image_cache[filename],
                'cached': True
            })
        
        # Load image
        filepath = os.path.join(ANOMALY_RESULTS_DIR, secure_filename(filename))
        if os.path.exists(filepath):
            base64_data = image_to_base64(filepath)
            if base64_data:
                # Cache the image
                image_cache[filename] = base64_data
                
                return jsonify({
                    'success': True,
                    'image': base64_data,
                    'cached': False
                })
        
        return jsonify({
            'success': False,
            'error': 'Image not found'
        })
        
    except Exception as e:
        app.logger.error(f"Error loading image {filename}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/anomaly-images')
def get_anomaly_images():
    """API endpoint to get optimized anomaly images with metadata."""
    try:
        # Get cached blockchain data
        current_time = time.time()
        blockchain_data = []
        
        with cache_lock:
            if (blockchain_cache['data'] is not None and 
                current_time - blockchain_cache['timestamp'] < blockchain_cache['ttl']):
                blockchain_data = blockchain_cache['data'].get('tx_logs', [])
            else:
                # Quick fetch if cache expired
                blockchain_data = blockchain_service.get_transaction_logs()
        
        # Get available images metadata first (fast)
        image_metadata = []
        if os.path.exists(ANOMALY_RESULTS_DIR):
            for filename in os.listdir(ANOMALY_RESULTS_DIR):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    filepath = os.path.join(ANOMALY_RESULTS_DIR, filename)
                    # Get file info without loading image
                    file_stats = os.stat(filepath)
                    
                    # Try to match with blockchain data
                    matched_tx = None
                    for tx in blockchain_data:
                        folder = tx.get('folder', '')
                        frame = tx.get('frame', 0)
                        error = tx.get('error', '')
                        
                        if folder.startswith('video_'):
                            video_num = folder.replace('video_', '')
                            expected_pattern = f"video_Test{video_num}_frame{frame:05d}_error{error}.jpg"
                            
                            if expected_pattern == filename:
                                matched_tx = tx
                                break
                    
                    image_metadata.append({
                        'filename': filename,
                        'size': file_stats.st_size,
                        'path': filepath,
                        'blockchain_match': matched_tx is not None,
                        'tx_data': matched_tx if matched_tx else {
                            'folder': 'Local File',
                            'frame': 0,
                            'error': 'N/A',
                            'index': -1
                        }
                    })
        
        return jsonify({
            'success': True,
            'images': image_metadata,
            'total_count': len(image_metadata)
        })
        
    except Exception as e:
        app.logger.error(f"Error loading image metadata: {e}")
        return jsonify({
            'success': False,
            'images': [],
            'total_count': 0,
            'error': str(e)
        })

@app.route('/api/blockchain-data')
def get_blockchain_data():
    """API endpoint to get cached blockchain data."""
    global blockchain_cache
    
    try:
        current_time = time.time()
        
        with cache_lock:
            # Check if cache is valid
            if (blockchain_cache['data'] is not None and 
                current_time - blockchain_cache['timestamp'] < blockchain_cache['ttl']):
                app.logger.info("Serving blockchain data from cache")
                return jsonify(blockchain_cache['data'])
        
        # Fetch fresh data
        app.logger.info("Fetching fresh blockchain data")
        anomaly_count = blockchain_service.get_anomaly_count()
        tx_logs = blockchain_service.get_transaction_logs()
        
        data = {
            'success': True,
            'anomaly_count': anomaly_count,
            'tx_logs': tx_logs,
            'cached': False
        }
        
        # Update cache
        with cache_lock:
            blockchain_cache['data'] = data
            blockchain_cache['timestamp'] = current_time
        
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f"Blockchain error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'anomaly_count': 0,
            'tx_logs': [],
            'cached': False
        })

