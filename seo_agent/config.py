import os
from pathlib import Path
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = BASE_DIR / "seo_agent" / "fixtures"
SAMPLES_DIR = BASE_DIR / "samples"

class Settings:
    # TinyFish API Config
    TINYFISH_API_KEY: str = os.getenv("TINYFISH_API_KEY", "")
    TINYFISH_FETCH_URL: str = os.getenv("TINYFISH_FETCH_URL", "https://api.fetch.tinyfish.ai")
    TINYFISH_SEARCH_URL: str = os.getenv("TINYFISH_SEARCH_URL", "https://api.search.tinyfish.ai")
    TINYFISH_AGENT_URL: str = os.getenv("TINYFISH_AGENT_URL", "https://agent.tinyfish.ai")
    
    # LLM Config (Provider-agnostic)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Execution & Limits
    DEFAULT_TIMEOUT: float = float(os.getenv("SEO_AGENT_TIMEOUT", "30.0"))
    MAX_STEPS: int = int(os.getenv("SEO_AGENT_MAX_STEPS", "12"))
    MOCK_MODE: bool = os.getenv("SEO_AGENT_MOCK", "false").lower() in ("1", "true", "yes")

settings = Settings()
