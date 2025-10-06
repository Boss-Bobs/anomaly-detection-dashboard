import os
import base64
import json
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app
from blockchain import BlockchainService
import time
from threading import Lock
import requests # NEW: Import for making HTTP requests to the RPi

# Initialize blockchain service
blockchain_service = BlockchainService()

# --- NEW: RPi Detector Configuration ---
# NOTE: Replace 'http://<RPi_PUBLIC_IP>:5000' with the actual public IP 
# or hostname/port of your Raspberry Pi detector service.
RPI_BASE_URL = os.getenv("RPI_BASE_URL", "http://192.168.235.162:5000") 
# ANOMALY_RESULTS_DIR is no longer needed as we fetch from the RPi
# ---------------------------------------

# Caching system
cache_lock = Lock()
blockchain_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 300  # 5 minutes cache
}
image_cache = {}

# --- Helper function for local images is no longer needed ---
# def image_to_base64(filepath):
#     ...

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

# --- This single image endpoint is no longer strictly needed for fetching RPi images
# --- because the RPi serves them directly. We can remove it or keep it for backward
# --- compatibility with old local files. Keeping it for now.
@app.route('/api/image/<filename>')
def get_single_image(filename):
    """API endpoint to get a single image on demand (Kept for compatibility)."""
    # This function is now superseded by direct calls to the RPi image API
    return jsonify({'success': False, 'error': 'This endpoint is deprecated. Use RPi image API directly.'}), 404

@app.route('/api/anomaly-images')
def get_anomaly_images():
    """
    API endpoint to fetch anomaly history and image URLs from the RPi detector.
    
    This function replaces the old local file system logic.
    """
    try:
        # 1. Fetch metadata (history) from the RPi's new API
        history_url = f"{RPI_BASE_URL}/api/rpi/history"
        app.logger.info(f"Fetching anomaly history from RPi: {history_url}")
        
        response = requests.get(history_url, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        history_data = response.json()
        
        if not history_data.get('success'):
            return jsonify({
                'success': False,
                'images': [],
                'total_count': 0,
                'error': history_data.get('error', 'RPi history fetch failed')
            })

        history_list = history_data.get('history', [])
        
        # 2. Process history to generate direct RPi image URLs
        anomaly_list = []
        for row in history_list:
            # Extract filename from the path column (assuming it's the last part)
            # Example path: '/home/anomalyproject/anomaly/anomaly_frames/2025-10-06 10-00-00.jpg'
            # The RPi endpoint is /api/rpi/image/<filename>
            full_path = row.get('4', '') 
            filename = os.path.basename(full_path)
            
            anomaly_list.append({
                'timestamp': row.get('1', 'N/A'), # Timestamp is in column 1 (if CSV is used)
                'score': row.get('2', 'N/A'),     # Score is in column 2
                'path': full_path,
                'frame_hash': row.get('5', 'N/A'), # Hash is in column 5
                # CRITICAL: This URL points directly to the RPi's image API
                'image_url': f"{RPI_BASE_URL}/api/rpi/image/{filename}",
                'filename': filename
            })

        # Reverse the list so the newest anomaly is first
        anomaly_list.reverse()
        
        return jsonify({
            'success': True,
            'images': anomaly_list,
            'total_count': len(anomaly_list)
        })

    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'images': [],
            'total_count': 0,
            'error': f"Failed to connect to RPi at {RPI_BASE_URL}. Is the RPi running and publicly accessible?"
        }), 503
    except Exception as e:
        app.logger.error(f"Error fetching RPi anomaly data: {e}")
        return jsonify({
            'success': False,
            'images': [],
            'total_count': 0,
            'error': str(e)
        })

@app.route('/api/blockchain-data')
def get_blockchain_data():
    """API endpoint to get cached blockchain data."""
    # This function remains unchanged as it talks to the BlockchainService, not the RPi
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
