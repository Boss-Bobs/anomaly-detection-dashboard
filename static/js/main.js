class AnomalyDashboard {
    constructor() {
        this.anomalyImages = {};
        this.imageMetadata = [];
        this.blockchainData = {};
        this.currentImageName = '';
        this.loadedImages = new Set();
        this.performanceStart = 0;
        this.initializeEventListeners();
        this.addPerformanceBadge();
    }

    initializeEventListeners() {
        // Main navigation buttons
        document.getElementById('showAnomalyBtn').addEventListener('click', () => {
            this.showSection('anomalyDisplay');
            this.loadAnomalyImages();
        });

        document.getElementById('showCountBtn').addEventListener('click', () => {
            this.showSection('countDisplay');
            this.loadStatistics();
        });

        document.getElementById('showTxHistoryBtn').addEventListener('click', () => {
            this.showSection('txHistoryDisplay');
            this.loadTransactionHistory();
        });

    }


    showSection(sectionId) {
        // Hide all sections
        const sections = ['anomalyDisplay', 'countDisplay', 'txHistoryDisplay'];
        sections.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.classList.add('section-hidden');
            }
        });

        // Show the selected section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.remove('section-hidden');
            targetSection.classList.add('fade-in');
        }
    }

    async loadAnomalyImages() {
        try {
            this.performanceStart = Date.now();
            this.showLoadingState('gallery');
            
            const response = await fetch('/api/anomaly-images');
            const data = await response.json();
            
            if (data.success) {
                this.imageMetadata = data.images;
                this.displayAnomalyGallery();
                
                const loadTime = (Date.now() - this.performanceStart) / 1000;
                this.showPerformanceMetric(loadTime);
                
                const blockchainCount = data.images.filter(img => img.blockchain_match).length;
                this.showSuccess(`🔗 ${blockchainCount} blockchain-verified frames | 📁 ${data.total_count} total frames`);
            } else {
                this.showError('Failed to load anomaly metadata');
            }
        } catch (error) {
            console.error('Error loading anomaly images:', error);
            this.showError('Failed to load anomaly frames from detection results');
        } finally {
            this.hideLoadingState('gallery');
        }
    }

    displayAnomalyGallery() {
        const thumbnailGrid = document.getElementById('thumbnailGrid');
        const mainImage = document.getElementById('mainAnomalyImage');
        const imageGallery = document.getElementById('imageGallery');
        const noImagesMessage = document.getElementById('noImagesMessage');

        if (this.imageMetadata.length === 0) {
            imageGallery.classList.add('d-none');
            noImagesMessage.classList.remove('d-none');
            return;
        }

        noImagesMessage.classList.add('d-none');
        imageGallery.classList.remove('d-none');

        // Clear existing thumbnails
        thumbnailGrid.innerHTML = '';

        // Create thumbnails with lazy loading
        this.imageMetadata.forEach((metadata, index) => {
            const thumbnailContainer = document.createElement('div');
            thumbnailContainer.className = 'thumbnail-container';
            
            const img = document.createElement('img');
            img.className = 'thumbnail loading';
            img.alt = metadata.filename;
            img.title = metadata.filename;
            
            // Add blockchain indicator
            if (metadata.blockchain_match) {
                img.classList.add('blockchain-matched');
                thumbnailContainer.setAttribute('data-blockchain', 'true');
            }
            
            // Placeholder while loading
            img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDE1MCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjE1MCIgaGVpZ2h0PSIxNTAiIGZpbGw9IiNmNmY2ZjYiLz48dGV4dCB4PSI3NSIgeT0iNzUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxMiIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkxvYWRpbmcuLi48L3RleHQ+PC9zdmc+';
            
            // Set first image as selected by default
            if (index === 0) {
                img.classList.add('selected');
                this.loadMainImage(metadata, img);
            }

            img.addEventListener('click', () => {
                this.selectThumbnail(img, metadata);
            });
            
            // Load thumbnail image lazily
            this.loadThumbnailImage(metadata.filename, img);
            
            thumbnailContainer.appendChild(img);
            thumbnailGrid.appendChild(thumbnailContainer);
        });
    }

    async selectThumbnail(imgElement, metadata) {
        // Remove selection from all thumbnails
        document.querySelectorAll('.thumbnail').forEach(thumb => {
            thumb.classList.remove('selected');
        });
        
        // Add selection to clicked thumbnail
        imgElement.classList.add('selected');
        
        // Load main image
        await this.loadMainImage(metadata, imgElement);
    }
    
    async loadMainImage(metadata, thumbnailImg) {
        const mainImage = document.getElementById('mainAnomalyImage');
        const imageInfo = document.getElementById('imageName');
        
        try {
            // Show loading state
            mainImage.style.opacity = '0.5';
            imageInfo.textContent = 'Loading image...';
            
            // Load full image
            const imageData = await this.loadImageData(metadata.filename);
            
            if (imageData) {
                mainImage.src = imageData;
                mainImage.style.opacity = '1';
                this.updateImageInfo(metadata);
                this.currentImageName = metadata.filename;
            }
        } catch (error) {
            console.error('Error loading main image:', error);
            imageInfo.textContent = 'Error loading image';
            mainImage.style.opacity = '1';
        }
    }
    
    async loadThumbnailImage(filename, imgElement) {
        try {
            const imageData = await this.loadImageData(filename);
            if (imageData) {
                imgElement.src = imageData;
                imgElement.classList.remove('loading');
            }
        } catch (error) {
            console.error(`Error loading thumbnail ${filename}:`, error);
            imgElement.classList.add('error');
        }
    }
    
    async loadImageData(filename) {
        // Check if already loaded
        if (this.loadedImages.has(filename)) {
            const cachedResponse = await fetch(`/api/image/${filename}`);
            const data = await cachedResponse.json();
            return data.success ? data.image : null;
        }
        
        // Load image
        const response = await fetch(`/api/image/${filename}`);
        const data = await response.json();
        
        if (data.success) {
            this.loadedImages.add(filename);
            return data.image;
        }
        
        return null;
    }
    
    updateImageInfo(metadata) {
        const txData = metadata.tx_data;
        let infoText;
        
        if (metadata.blockchain_match) {
            infoText = `🔗 ${metadata.filename} | ${txData.folder} Frame ${txData.frame} | Error: ${txData.error}`;
        } else {
            infoText = `📁 ${metadata.filename} | Local file (${(metadata.size / 1024).toFixed(1)} KB)`;
        }
        
        document.getElementById('imageName').textContent = infoText;
    }


    async loadStatistics() {
        // Count local images
        const localCount = Object.keys(this.anomalyImages).length;
        document.getElementById('localCount').textContent = localCount;

        // Load blockchain data
        try {
            const response = await fetch('/api/blockchain-data');
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('blockchainCount').textContent = data.anomaly_count;
                document.getElementById('blockchainStatus').innerHTML = 
                    '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Connected to Sepolia</span>';
                this.blockchainData = data;
            } else {
                document.getElementById('blockchainCount').textContent = 'N/A';
                document.getElementById('blockchainStatus').innerHTML = 
                    '<span class="badge bg-danger"><i class="fas fa-times me-1"></i>Connection Failed</span>';
            }
        } catch (error) {
            console.error('Error loading blockchain data:', error);
            document.getElementById('blockchainCount').textContent = 'N/A';
            document.getElementById('blockchainStatus').innerHTML = 
                '<span class="badge bg-danger"><i class="fas fa-times me-1"></i>Connection Error</span>';
        }
    }

    async loadTransactionHistory() {
        const loading = document.getElementById('txLoading');
        const content = document.getElementById('txContent');
        const error = document.getElementById('txError');

        // Show loading state
        loading.classList.remove('d-none');
        content.classList.add('d-none');
        error.classList.add('d-none');

        try {
            const response = await fetch('/api/blockchain-data');
            const data = await response.json();

            loading.classList.add('d-none');

            if (data.success) {
                content.classList.remove('d-none');
                this.displayTransactionHistory(data.tx_logs);
            } else {
                error.classList.remove('d-none');
                document.getElementById('errorMessage').textContent = 
                    data.error || 'Unable to connect to the blockchain.';
            }
        } catch (err) {
            loading.classList.add('d-none');
            error.classList.remove('d-none');
            document.getElementById('errorMessage').textContent = 
                'Network error. Please check your connection.';
        }
    }

    displayTransactionHistory(txLogs) {
        const txHistory = document.getElementById('txHistory');
        const noTransactions = document.getElementById('noTransactions');

        if (txLogs.length === 0) {
            txHistory.innerHTML = '';
            noTransactions.classList.remove('d-none');
            return;
        }

        noTransactions.classList.add('d-none');
        txHistory.innerHTML = '';

        txLogs.forEach((log, index) => {
            const txItem = document.createElement('div');
            txItem.className = 'transaction-item';
            
            txItem.innerHTML = `
                <div class="tx-header">
                    <span class="tx-index">#${log.index || index}</span>
                    <span class="tx-timestamp">
                        <i class="fas fa-clock me-1"></i>
                        ${log.timestamp}
                    </span>
                </div>
                <div class="tx-details">
                    <div class="tx-detail">
                        <div class="tx-detail-label">Folder</div>
                        <div class="tx-detail-value">${log.folder}</div>
                    </div>
                    <div class="tx-detail">
                        <div class="tx-detail-label">Frame</div>
                        <div class="tx-detail-value">${log.frame}</div>
                    </div>
                    <div class="tx-detail">
                        <div class="tx-detail-label">Error Type</div>
                        <div class="tx-detail-value">${log.error}</div>
                    </div>
                </div>
            `;

            txHistory.appendChild(txItem);
        });
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'error');
    }

    showLoadingState(section) {
        const loadingHtml = `
            <div class="loading-overlay" id="${section}Loading">
                <div class="loading-spinner">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Processing anomaly data...</p>
                </div>
            </div>
        `;
        
        const targetSection = document.getElementById(`${section}Display`) || document.body;
        const loadingDiv = document.createElement('div');
        loadingDiv.innerHTML = loadingHtml;
        targetSection.appendChild(loadingDiv.firstElementChild);
    }
    
    hideLoadingState(section) {
        const loadingOverlay = document.getElementById(`${section}Loading`);
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }
    
    showAlert(message, type) {
        const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
        const icon = type === 'error' ? '⚠️' : '✅';
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show modern-alert" role="alert">
                <span class="alert-icon">${icon}</span>
                <span class="alert-message">${message}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const container = document.querySelector('.container-fluid');
        const firstChild = container.firstElementChild;
        const alertDiv = document.createElement('div');
        alertDiv.innerHTML = alertHtml;
        container.insertBefore(alertDiv, firstChild);

        // Auto-dismiss after 4 seconds for success, 6 for error
        const timeout = type === 'error' ? 6000 : 4000;
        setTimeout(() => {
            const alert = alertDiv.querySelector('.alert');
            if (alert) {
                alert.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }
        }, timeout);
    }
    
    addPerformanceBadge() {
        const badge = document.createElement('div');
        badge.className = 'performance-badge';
        badge.id = 'performanceBadge';
        badge.innerHTML = '🚀 Optimized Dashboard';
        document.body.appendChild(badge);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            badge.style.opacity = '0';
            setTimeout(() => badge.remove(), 500);
        }, 5000);
    }
    
    showPerformanceMetric(loadTime) {
        const badge = document.getElementById('performanceBadge');
        if (badge) {
            badge.innerHTML = `⚡ Loaded in ${loadTime.toFixed(1)}s`;
            badge.style.backgroundColor = loadTime < 2 ? 'rgba(40, 167, 69, 0.9)' : 
                                         loadTime < 5 ? 'rgba(255, 193, 7, 0.9)' : 
                                         'rgba(220, 53, 69, 0.9)';
        }
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AnomalyDashboard();
});
