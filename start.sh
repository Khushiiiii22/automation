#!/bin/bash
# Launch the professional booking automation web interface

cd "$(dirname "$0")"
echo "🚀 Starting Appointment Booking Automation System..."
echo "📱 Opening web interface at http://localhost:5001"
echo "Press Ctrl+C to stop the server"
echo ""

.venv/bin/python app.py
