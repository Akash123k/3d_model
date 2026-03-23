#!/bin/bash

# Script to restart the backend server

echo "Stopping existing backend server..."
sudo pkill -f "uvicorn app.main:app"

sleep 2

echo "Starting backend server on port 8283..."
cd /home/venom/akash/3d_model/backend
source ../myenv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8283 --reload
