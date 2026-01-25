#!/bin/bash
# Start Streamlit Messenger App on VPS

# Install dependencies if needed
pip install -r requirements.txt

# Run Streamlit (use nohup to keep running after disconnect)
nohup streamlit run app.py --server.address 0.0.0.0 --server.port 8501 > streamlit.log 2>&1 &

echo "✅ Server started on port 8501"
echo "📧 Access at: http://$(hostname -I | awk '{print $1}'):8501"
echo "📄 Logs: tail -f streamlit.log"
