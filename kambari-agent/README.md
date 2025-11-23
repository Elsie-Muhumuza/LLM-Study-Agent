# Kambari Altar Agent

An intelligent agent for managing and automating Bible study groups, role assignments, and study material generation using Google's Gemini AI.

## Features

- **Automated Role Assignment**: Fairly assigns roles (prayer lead, scripture reader, sharing lead) to group members
- **AI-Powered Question Generation**: Generates thoughtful discussion questions using Google's Gemini AI
- **Study Material Management**: Create and manage Bible study series and passages
- **Scheduling**: Schedule study sessions and track attendance
- **WhatsApp Integration**: Send reminders and study materials via WhatsApp
- **Web Interface**: User-friendly Streamlit-based web interface

## Prerequisites

- Python 3.11+
- Google Gemini API key
- pip (Python package manager)
- SQLite (included with Python)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kambari-altar-agent.git
   cd kambari-altar-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your Google Gemini API key
   - Configure other settings as needed

## Usage

### Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run main.py
   ```

2. Open your browser to `http://localhost:8501`

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t kambari-agent .
   ```

2. Run the container:
   ```bash
   docker run -p 8501:8501 --env-file .env kambari-agent
   ```

## Project Structure

```
kambari-agent/
├── app/
│   ├── __init__.py
│   ├── db.py           # Database models and operations
│   ├── kambari_agent.py # Main application logic
│   ├── question_generator.py # AI question generation
│   └── roles_engine.py  # Role assignment logic
├── data/
│   └── study_guides/   # Generated study guides
├── .env.example        # Example environment variables
├── .gitignore
├── Dockerfile
├── main.py             # Application entry point
├── README.md
└── requirements.txt    # Python dependencies
```

## Configuration

Copy `.env.example` to `.env` and update the following variables:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
DEBUG=True
DATABASE_URL=sqlite:///kambari.db
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini for AI capabilities
- Streamlit for the web interface
- SQLAlchemy for database operations