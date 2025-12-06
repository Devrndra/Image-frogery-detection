# Image Authentication System

A full-stack web application for detecting digital image tampering using Deep Learning (Dual-Stream CNN) and Classical Forensics (ELA & Hashing).

## Features
1.  **Forgery Detection**: Uses Error Level Analysis (ELA) and a CNN to detect manipulated regions.
2.  **Integrity Check**: Uses Perceptual Hashing to detect even pixel-level modifications (cropping, resizing).
3.  **User-Friendly UI**: React-based frontend for easy interaction.

## Prerequisites
Before running the project, ensure you have the following installed:
1.  **Python 3.11**: [Download Here](https://www.python.org/downloads/release/python-3110/)
    *   *Important*: During installation, check "Add Python to PATH".
2.  **Node.js (LTS Version)**: [Download Here](https://nodejs.org/)

## Installation Guide

1.  **Unzip the Project**: Extract the project folder to your Desktop.

2.  **Open Terminal**:
    *   Open Command Prompt (cmd) or PowerShell.
    *   Navigate to the project folder:
        ```bash
        cd "path/to/ronaldo project"
        ```

3.  **Install Backend Dependencies**:
    ```bash
    py -3.11 -m pip install -r requirements.txt
    ```

4.  **Install Frontend Dependencies**:
    ```bash
    cd frontend
    npm install
    cd ..
    ```

## How to Run
Simply double-click the **`start_app.bat`** file in the project folder.

Alternatively, run this command in the project root:
```bash
.\start_app.bat
```

This will launch:
*   **Backend API**: http://localhost:8000
*   **Frontend UI**: http://localhost:5173

## Troubleshooting
*   **"Python not found"**: Ensure Python 3.11 is installed and added to PATH.
*   **"npm is not recognized"**: Ensure Node.js is installed.
