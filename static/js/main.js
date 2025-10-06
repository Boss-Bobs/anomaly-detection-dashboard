document.addEventListener('DOMContentLoaded', () => {
    // Determine RPi Base URL from the current environment (must match server-side logic)
    // NOTE: This client-side variable is only for fallback/visual clarity. The server (routes.py)
    // manages the official RPI_BASE_URL. We use a placeholder here.
    const RPI_BASE_URL = 'https://relativistic-kacie-puffingly.ngrok-free.dev'; // Placeholder for the actual public IP set in RENDER ENV

    // --- Core Functions ---
    
    function fetchAndDisplayAnomalies() {
        const statusDiv = document.getElementById('anomalyStatus');
        const imagesRow = document.getElementById('anomalyImagesRow');
        const noAnomalies = document.getElementById('noAnomalies');
        const anomalyError = document.getElementById('anomalyError');
        const anomalyErrorMessage = document.getElementById('anomalyErrorMessage');

        // Show loading, hide others
        statusDiv.classList.remove('d-none');
        imagesRow.classList.add('d-none');
        noAnomalies.classList.add('d-none');
        anomalyError.classList.add('d-none');

        fetch('/api/anomaly-images')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                statusDiv.classList.add('d-none');
                imagesRow.innerHTML = '';

                if (!data.success) {
                    anomalyErrorMessage.textContent = data.error || 'Unknown RPi error.';
                    anomalyError.classList.remove('d-none');
                    return;
                }

                if (data.images.length === 0) {
                    noAnomalies.classList.remove('d-none');
                } else {
                    data.images.forEach(anomaly => {
                        const card = createAnomalyCard(anomaly);
                        imagesRow.appendChild(card);
                    });
                    imagesRow.classList.remove('d-none');
                }
            })
            .catch(error => {
                statusDiv.classList.add('d-none');
                anomalyErrorMessage.textContent = `Could not connect to RPi via Render: ${error.message}. Check RPI_BASE_URL configuration.`;
                anomalyError.classList.remove('d-none');
                console.error('Error fetching anomaly images:', error);
            });
    }

    function createAnomalyCard(anomaly) {
        const col = document.createElement('div');
        col.className = 'col';

        // CRITICAL: img src points directly to the RPi's API
        col.innerHTML = `
            <div class="card h-100 shadow-sm anomaly-card">
                <img src="${anomaly.image_url}" class="card-img-top anomaly-img" alt="Anomaly Detected" loading="lazy">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">${anomaly.timestamp}</h6>
                    <p class="card-text">
                        <strong>Score:</strong> <span class="badge bg-danger">${anomaly.score}</span><br>
                        <strong>Hash:</strong> <span class="hash-text">${anomaly.frame_hash.substring(0, 12)}...</span>
                    </p>
                </div>
            </div>
        `;
        return col;
    }

    function fetchAndDisplayBlockchain() {
        const txLoader = document.getElementById('txLoader');
        const txContent = document.getElementById('txContent');
        const txHistory = document.getElementById('txHistory');
        const noTransactions = document.getElementById('noTransactions');
        const txError = document.getElementById('txError');
        const totalTxs = document.getElementById('totalTxs');

        // Show loading, hide others
        txLoader.classList.remove('d-none');
        txContent.classList.add('d-none');
        txError.classList.add('d-none');

        fetch('/api/blockchain-data')
            .then(response => response.json())
            .then(data => {
                txLoader.classList.add('d-none');
                txContent.classList.remove('d-none');
                
                if (!data.success) {
                    document.getElementById('errorMessage').textContent = data.error;
                    txError.classList.remove('d-none');
                    totalTxs.textContent = '--';
                    return;
                }
                
                totalTxs.textContent = data.anomaly_count;
                txHistory.innerHTML = '';

                if (data.tx_logs.length === 0) {
                    noTransactions.classList.remove('d-none');
                } else {
                    noTransactions.classList.add('d-none');
                    data.tx_logs.reverse().forEach(log => {
                        const txItem = createTransactionItem(log);
                        txHistory.appendChild(txItem);
                    });
                }
            })
            .catch(error => {
                txLoader.classList.add('d-none');
                txError.classList.remove('d-none');
                document.getElementById('errorMessage').textContent = `Failed to fetch blockchain data: ${error}`;
                totalTxs.textContent = '--';
                console.error('Error fetching blockchain data:', error);
            });
    }

    function createTransactionItem(log) {
        const item = document.createElement('div');
        item.className = 'transaction-item mb-3 p-3 border rounded';

        // Map contract fields to human-readable labels
        const score = log.error;
        const timestamp = log.folder;
        const hash = log.frame; 
        
        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <i class="fas fa-check-circle text-success me-2"></i>
                    <strong>Anomaly Recorded</strong>
                </div>
                <small class="text-muted">${timestamp}</small>
            </div>
            <div class="mt-2 small">
                <p class="mb-1"><strong>Score:</strong> <span class="badge bg-warning text-dark">${score}</span></p>
                <p class="mb-0"><strong>Frame ID (uint256):</strong> <span class="text-break">${hash}</span></p>
            </div>
        `;
        return item;
    }

    // --- NEW: Function to set up the RPi Live Video Feed ---
    function setupLiveVideoFeed() {
    const videoFeed = document.getElementById('liveVideoFeed');
    const videoErrorMessage = document.getElementById('video-error-message');

    const RPI_STREAM_URL = 'https://relativistic-kacie-puffingly.ngrok-free.dev';

    // Connect to WebSocket namespace
    const socket = io(RPI_STREAM_URL + '/ws/video_feed', {
        transports: ['websocket'],
        extraHeaders: {
            'ngrok-skip-browser-warning': 'true'  // Bypass ngrok warning if needed
        }
    });

    socket.on('connect', () => {
        console.log('Connected to RPi WebSocket');
        videoErrorMessage.textContent = 'Live Stream Active. Latency depends on network.';
        videoErrorMessage.classList.remove('text-danger');
        videoErrorMessage.classList.add('text-success');
    });

    socket.on('video_frame', (jsonData) => {
        const data = JSON.parse(jsonData);
        videoFeed.src = `data:image/jpeg;base64,${data.frame}`;
        // Optional: Handle anomaly overlay or alerts
        if (data.is_anomaly) {
            console.log(`Anomaly detected! Score: ${data.anomaly_score}`);
            // You could add a red border or alert here
        }
    });

    socket.on('disconnect', () => {
        videoErrorMessage.textContent = 'Disconnected from RPi WS. Check ngrok/RPi.';
        videoErrorMessage.classList.add('text-danger');
        videoErrorMessage.classList.remove('text-success');
    });

    socket.on('connect_error', (err) => {
        videoErrorMessage.textContent = `Failed to connect to RPi WS: ${err.message}. Check ngrok/RPi.`;
        videoErrorMessage.classList.add('text-danger');
        videoErrorMessage.classList.remove('text-success');
        console.error('WebSocket connect error:', err);
    });
}

    // --- Initialization and Event Listeners ---
    fetchAndDisplayAnomalies();
    fetchAndDisplayBlockchain();
    
    // Set up listeners for manual refresh
    document.getElementById('refreshAnomalies').addEventListener('click', fetchAndDisplayAnomalies);
    document.getElementById('refreshBlockchain').addEventListener('click', fetchAndDisplayBlockchain);

    // Set up listeners for tab changes (Only call setupLiveVideoFeed when the live tab is actively shown)
    const mainTab = document.getElementById('mainTab');
    mainTab.addEventListener('shown.bs.tab', (event) => {
        if (event.target.id === 'live-tab') {
            setupLiveVideoFeed();
        }
    });
});
