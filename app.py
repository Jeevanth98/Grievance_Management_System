"""
app.py - Root entry point for Grievance Management System Admin Portal.
Sets wide layout immediately and delegates to admin_portal.
"""

import sys
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

# Must be the very first Streamlit call in the entrypoint script!
st.set_page_config(
    page_title="Grievance Admin Portal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from admin_portal.app import main

if __name__ == "__main__":
    main()
