# main.py
"""
Main entry point for running the Kambari Altar Agent as a Streamlit application.
Run from the project root directory using:
    streamlit run main.py
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import the app
from app.kambari_agent import main

if __name__ == "__main__":
    main()