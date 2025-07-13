"""Configuration handling for YouTube MCP server"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class Config(BaseModel):
    """Server configuration"""
    config_dir: str = Field(description="Configuration directory path")
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
        
        # Get configuration directory
        config_dir = os.environ.get("CONFIG_DIR")
        
        # Create config directory if it exists
        if config_dir:
            config_dir_path = Path(config_dir)
            config_dir_path.mkdir(exist_ok=True)
            # Client secrets and token files are in CONFIG_DIR
            client_secrets_file = str(config_dir_path / "client_secrets.json")
            token_file = str(config_dir_path / "token.json")
        else:
            client_secrets_file = None
            token_file = None
        
        return cls(
            config_dir=config_dir,
            client_secrets_file=client_secrets_file,
            token_file=token_file,
            raw_transcript_lang=os.environ.get("YOUTUBE_RAW_TRANSCRIPT_LANG"),
            gemini_model=os.environ.get("GEMINI_MODEL"),
            gemini_api_key=os.environ.get("GEMINI_API_KEY"),
            upload_state_dir=os.environ.get("YOUTUBE_UPLOAD_STATE_DIR")
        )
    
