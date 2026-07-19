# Weather Assistant AI

## Project Overview
Weather Assistant AI is an intelligent, conversational agent designed to provide real-time weather and time information. Built using the Google Agent Development Kit (ADK) and powered by Groq's `llama-3.3-70b-versatile` model, it features a graph-based workflow architecture that seamlessly handles structured queries without relying on fragile LLM tool-calling.

## Features
- **Accurate Weather Info:** Simulated current weather data for major cities.
- **Real-Time Clocks:** Local time resolution with timezone awareness.
- **Workflow Graph Architecture:** A 3-node ADK Workflow (`query_parser` -> `tool_executor` -> `response_generator`) that guarantees reliable execution and bypasses LLM tool formatting errors.
- **ADK Web UI Integration:** Out-of-the-box local development server and chat interface.
- **Groq Llama 3.3 Integration:** Ultra-fast, intelligent natural language understanding and generation.

## Tech Stack
- **Python:** 3.11+
- **Google ADK (Agent Development Kit):** Framework for building and running AI agents.
- **LiteLLM:** Used as an abstraction layer for model interactions.
- **Groq API:** Hosting the `llama-3.3-70b-versatile` model.
- **FastAPI / Uvicorn:** Under the hood for ADK web server.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HafizaAmnaNaseem/weather-assistant-ai.git
   cd weather-assistant-ai
   ```

2. **Set up the virtual environment:**
   Using `uv` (recommended) or standard `pip`:
   ```bash
   uv sync
   # or
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Environment Variables
Create a `.env` file in the root of the project:
```env
GROQ_API_KEY="your_groq_api_key_here"
```

## Groq API Setup
To run this project, you need an API key from Groq:
1. Go to [Groq Console](https://console.groq.com/).
2. Create an account and generate a new API key.
3. Add the key to your `.env` file.

## Local Run Instructions

**Option 1 — Use the included batch script (recommended on Windows):**
```bat
.\run_weather.bat
```

**Option 2 — Run manually from the terminal:**
```bash
uv run python -m google.adk.cli web . --host 127.0.0.1 --port 8000
```

Then open your browser and go to: **http://127.0.0.1:8000/dev-ui**

## Usage Examples
In the ADK Dev UI chat, you can ask:
- *"What is the weather in Faisalabad?"*
- *"Tell me the time in London."*
- *"What's the weather like in Tokyo?"*
- *"What time is it in New York?"*
- *"What is the current time in Sydney?"*

### Supported Cities for `get_weather`
Faisalabad, Lahore, Karachi, Islamabad, San Francisco, New York, London, Tokyo, Paris, Berlin, Sydney, Dubai, Mumbai, Beijing.
Any other city returns a generic fallback response.

### Supported Cities for `get_current_time`
San Francisco, Los Angeles, New York, Chicago, London, Paris, Berlin, Istanbul, Moscow, Dubai, Faisalabad/Pakistan, Mumbai/India, Beijing, Tokyo, Sydney, Singapore, Hong Kong, Seoul.
Unrecognised cities return a helpful list of supported locations.

## Project Structure
```
weather-assistant-ai/
├── app/
│   ├── __init__.py
│   └── agent.py       # Core Workflow and Node definitions
├── pyproject.toml     # Dependencies and project metadata
├── .env.example       # Example environment variables
└── README.md
```

## Future Improvements
- Integrate live external weather API (e.g. OpenWeatherMap).
- Expand location coverage and geolocation features.
- Deploy to Hugging Face or Google Cloud Run.

## License
MIT License

## Author
Hafiza Amna
