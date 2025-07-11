"""Configuration handling for YouTube MCP server"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Default configuration directory name
DEFAULT_CONFIG_DIR_NAME = ".pmind-youtube-mcp"


def get_default_config_dir() -> Path:
    """Get the default configuration directory"""
    # Check for CONFIG_DIR environment variable first
    config_dir_env = os.environ.get("CONFIG_DIR")
    if config_dir_env:
        return Path(config_dir_env)
    # Otherwise use default in home directory
    return Path.home() / DEFAULT_CONFIG_DIR_NAME


class Config(BaseModel):
    """Server configuration"""
    client_secrets_file: str = Field(description="Path to OAuth client secrets file")
    token_file: str = Field(description="Path to OAuth token file")
    raw_transcript_lang: str = Field(description="Default language for raw transcript extraction")
    gemini_model: str = Field(description="Default Gemini model to use")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key for AI integration")
    upload_state_dir: str = Field(description="Directory for storing upload state files")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        # Load .env file if it exists
        load_dotenv()
        
        # Default config directory
        config_dir = get_default_config_dir()
        config_dir.mkdir(exist_ok=True)
        
        # Get configuration values
        # Client secrets and token files are always in CONFIG_DIR
        client_secrets_file = str(config_dir / "client_secrets.json")
        token_file = str(config_dir / "token.json")
        raw_transcript_lang = os.environ.get("YOUTUBE_RAW_TRANSCRIPT_LANG", "en")
        gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        upload_state_dir = os.environ.get(
            "YOUTUBE_UPLOAD_STATE_DIR", 
            "/tmp/pmind-youtube-mcp-uploads"
        )
        
        return cls(
            client_secrets_file=client_secrets_file,
            token_file=token_file,
            raw_transcript_lang=raw_transcript_lang,
            gemini_model=gemini_model,
            gemini_api_key=gemini_api_key,
            upload_state_dir=upload_state_dir
        )
    
