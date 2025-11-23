#!/usr/bin/env python3
"""
Kambari Altar Agent - Main Entry Point

This module serves as the entry point for the Kambari Altar Agent application.
It initializes the environment and starts the appropriate interface.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'kambari_agent.log')
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file if it exists."""
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info("Loaded environment variables from %s", env_path)
    else:
        logger.warning("No .env file found. Using system environment variables.")

def check_requirements():
    """Check if all required environment variables are set."""
    required_vars = [
        'GEMINI_API_KEY',
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("Missing required environment variables: %s", 
                    ", ".join(missing_vars))
        logger.info("Please create a .env file with the required variables.")
        logger.info("See .env.example for reference.")
        sys.exit(1)

def run():
    """Run the Kambari Altar Agent."""
    try:
        # Load environment variables
        load_environment()
        
        # Check requirements
        check_requirements()
        
        # Import the Streamlit app
        from app.kambari_agent import run_streamlit_app
        
        # Start the Streamlit app
        logger.info("Starting Kambari Altar Agent...")
        run_streamlit_app()
        
    except ImportError as e:
        logger.error("Failed to import required modules: %s", str(e))
        logger.info("Please make sure all dependencies are installed.")
        logger.info("Run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    run()
