"""
MrJet WebGUI – Entry Point

Usage
-----
    streamlit run main.py
"""

from app.ui import setup_page, render

# ---- Streamlit page configuration (must happen first) ----
setup_page()

# ---- Render the application UI ----
render()