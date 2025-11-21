# main.py
"""
Main entry point for the Kambari Altar Agent.
Run with: streamlit run main.py
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set environment variables for Streamlit Cloud
os.environ["DB_PATH"] = str(Path(project_root, "kambari.db"))
os.environ["PARABLES_JSON"] = str(Path(project_root, "data", "builtin_parables.json"))

# Now import the app
try:
    from app.kambari_agent import main
except ImportError:
    # Try relative import if absolute import fails
    from .app.kambari_agent import main

if __name__ == "__main__":
    # Check if running in Streamlit
    if "STREAMLIT_CLOUD" in os.environ:
        # Running in Streamlit Cloud
        main()
    else:
        # Running locally
        from app.kambari_agent import run_streamlit
        run_streamlit()