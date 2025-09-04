# Anomaly Detection Dashboard

## Overview

This is a Flask-based web application that serves as an Anomaly Detection Dashboard. It uses a 3D Convolutional Autoencoder for detecting anomalies in images and integrates with blockchain technology to log anomaly findings immutably. The application provides a user-friendly interface for uploading anomaly images, viewing detection results, and tracking blockchain transactions related to anomaly logging.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with a responsive Bootstrap 5 UI
- **Styling**: Custom CSS with gradient designs and modern card-based layouts
- **JavaScript**: Vanilla JavaScript implementing a dashboard class for client-side interactions
- **File Upload**: Drag-and-drop interface with support for PNG, JPG, JPEG, and GIF formats
- **Real-time Updates**: Dynamic content loading for anomaly displays and statistics

### Backend Architecture
- **Framework**: Flask web framework with modular route organization
- **File Handling**: Secure file uploads with size limits (16MB max) and filename sanitization
- **Session Management**: Flask sessions with configurable secret keys
- **Error Handling**: Comprehensive logging with flash message system
- **API Structure**: RESTful endpoints for file uploads, image processing, and data retrieval

### Data Storage Solutions
- **File Storage**: Local filesystem storage in an `uploads/` directory
- **Image Processing**: Base64 encoding for efficient image transmission and display
- **Configuration**: Environment variable-based configuration with fallback defaults

### Blockchain Integration
- **Web3 Provider**: Ethereum blockchain integration via Infura (Sepolia testnet)
- **Smart Contract**: Custom contract for logging anomaly detection results
- **Contract Functions**: 
  - `logAnomaly()` for recording new anomaly findings
  - `getAnomaly()` for retrieving historical anomaly records
- **Immutable Logging**: Permanent record of anomaly detections with folder, frame index, and error details

### Authentication and Authorization
- **Session Security**: Flask session management with configurable secret keys
- **File Security**: Secure filename handling and file type validation
- **Environment Security**: Sensitive configuration data managed through environment variables

## External Dependencies

### Blockchain Services
- **Infura**: Ethereum node provider for blockchain connectivity
- **Web3.py**: Python library for Ethereum blockchain interactions
- **Smart Contract**: Deployed on Sepolia testnet at address `0x279FcACc1eB244BBD7Be138D34F3f562Da179dd5`

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome 6**: Icon library for UI elements
- **Modern Browsers**: HTML5 and ES6+ JavaScript features

### Python Dependencies
- **Flask**: Core web framework
- **Werkzeug**: WSGI utilities for secure file handling
- **Web3**: Ethereum blockchain integration
- **Base64**: Image encoding/decoding for efficient data transfer

### Development Tools
- **Logging**: Python's built-in logging module for debugging and monitoring
- **OS Module**: Environment variable management and file system operations