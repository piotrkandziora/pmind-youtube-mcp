"""Main MCP server implementation using FastMCP"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from fastmcp import FastMCP
from .config import Config
from .services import (
    videos, channels, playlists, transcripts, subscriptions, search,
    captions, channel_banners, channel_sections, comments, comment_threads,
    members, memberships_levels, playlist_items, playlist_images,
    thumbnails, video_categories, watermarks, i18n_regions, i18n_languages, gemini
)
from .utils import YouTubeClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the MCP server"""
    # Load configuration
    logger.debug("Loading configuration from environment...")
    try:
        config = Config.from_env()
        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {type(e).__name__}: {str(e)}")
        raise
    
    # Initialize FastMCP server
    mcp = FastMCP(
        name="PMIND MCP Youtube Server",
        instructions="""
This server provides YouTube Data API access through MCP tools.

Available tools:

Videos:
- videos_list: List videos by ID, chart, or rating
- videos_get_rating: Get user's ratings for videos
- videos_rate: Like, dislike, or remove rating from video
- videos_update: Update video metadata
- videos_delete: Delete a video
- videos_report_abuse: Report abusive video content

Channels:
- channels_get_channel: Get channel information
- channels_list_videos: List videos from a channel
- channels_list: List channels by various criteria
- channels_update: Update channel metadata

Playlists:
- playlists_list: List playlists by channel, ID, or owned by user
- playlists_insert: Create a new playlist
- playlists_update: Update playlist metadata
- playlists_delete: Delete a playlist
- playlists_get_playlist: [DEPRECATED] Get playlist info (use playlists_list)

Playlist Items:
- playlist_items_list: List playlist items with filters
- playlist_items_insert: Add video to playlist
- playlist_items_update: Update playlist item (position, etc.)
- playlist_items_delete: Remove video from playlist

Playlist Images:
- playlist_images_list: List playlist thumbnail images
- playlist_images_insert: Upload playlist thumbnail
- playlist_images_update: Update playlist thumbnail
- playlist_images_delete: Delete playlist thumbnail

Search:
- search_list: Comprehensive YouTube search with all filters

Subscriptions:
- subscriptions_list_channel_subscriptions: List channel subscriptions
- subscriptions_list_my_subscriptions: List your subscriptions
- subscriptions_list_my_recent_subscribers: List recent subscribers
- subscriptions_insert: Subscribe to a channel
- subscriptions_delete: Unsubscribe from a channel

Captions:
- captions_list: List caption tracks for a video
- captions_download: Download caption content
- captions_update: Update caption metadata
- captions_delete: Delete a caption track

Channel Management:
- channel_banners_insert: Upload channel banner
- channel_sections_list: List channel sections
- channel_sections_insert: Create channel section
- channel_sections_update: Update channel section
- channel_sections_delete: Delete channel section

Comments:
- comments_list: List comment replies
- comments_insert: Reply to a comment
- comments_update: Update a comment
- comments_delete: Delete a comment
- comments_set_moderation_status: Moderate comments

Comment Threads:
- comment_threads_list: List top-level comments
- comment_threads_insert: Create new comment

Memberships:
- members_list: List channel members
- memberships_levels_list: List membership levels

Media Management:
- thumbnails_set: Upload video thumbnail
- watermarks_set: Set channel watermark
- watermarks_unset: Remove channel watermark

Metadata:
- video_categories_list: List video categories by region
- i18n_regions_list: List supported YouTube regions
- i18n_languages_list: List supported YouTube UI languages

Other:
- transcripts_get_transcript: Get raw transcript/captions from YouTube (no auth required)

Gemini AI Integration:
- gemini_analyze_youtube_video: Analyze YouTube videos using Gemini AI
- gemini_compare_youtube_videos: Compare multiple YouTube videos (2-10)
- gemini_video_qa: Ask questions about a YouTube video
- gemini_video_transcript: Generate transcripts using Gemini's video understanding

Configuration:
- CONFIG_DIR: Configuration directory containing client_secrets.json and token.json
- YOUTUBE_RAW_TRANSCRIPT_LANG: Default language for raw transcripts (default: 'en')
- YOUTUBE_UPLOAD_STATE_DIR: Directory for upload state files (default: '/tmp/pmind-youtube-mcp-uploads')
- GEMINI_MODEL: Default Gemini model to use (default: 'gemini-2.5-flash')
- GEMINI_API_KEY: API key for Gemini AI integration

OAuth Authentication:
- First run will open browser for Google login
- Token is saved to the configured token file path
- All operations require OAuth authentication
        """
    )
    
    # Create a single YouTube client instance with OAuth
    logger.debug("Creating shared YouTube client with OAuth...")
    youtube_client = YouTubeClient(
        client_secrets_file=config.client_secrets_file,
        token_file=config.token_file
    )
    
    # Store config and client in server state for tools to access
    mcp.state = {"config": config, "youtube_client": youtube_client}
    
    # Register all tools with the shared client
    videos.register_tools(mcp, config, youtube_client)
    channels.register_tools(mcp, config, youtube_client)
    playlists.register_tools(mcp, config, youtube_client)
    playlist_items.register_tools(mcp, config, youtube_client)
    playlist_images.register_tools(mcp, config, youtube_client)
    subscriptions.register_tools(mcp, config, youtube_client)
    search.register_tools(mcp, config, youtube_client)
    captions.register_tools(mcp, config, youtube_client)
    channel_banners.register_tools(mcp, config, youtube_client)
    channel_sections.register_tools(mcp, config, youtube_client)
    comments.register_tools(mcp, config, youtube_client)
    comment_threads.register_tools(mcp, config, youtube_client)
    members.register_tools(mcp, config, youtube_client)
    memberships_levels.register_tools(mcp, config, youtube_client)
    thumbnails.register_tools(mcp, config, youtube_client)
    video_categories.register_tools(mcp, config, youtube_client)
    watermarks.register_tools(mcp, config, youtube_client)
    i18n_regions.register_tools(mcp, config, youtube_client)
    i18n_languages.register_tools(mcp, config, youtube_client)
    transcripts.register_tools(mcp, config)
    gemini.register_tools(mcp, config)
    
    return mcp


def configure_interactive():
    """Interactive configuration wizard"""
    print("\nPMIND Youtube MCP Configuration")
    print("=" * 40)
    print("\nThis wizard will help you set up the PMIND MCP Youtube server.\n")
    
    # Get configuration values
    # Calculate default paths based on user's home directory
    default_config_dir = Path.home() / ".pmind-youtube-mcp"
    default_upload_dir = Path("/tmp") / "pmind-youtube-mcp-uploads"
    
    # Ask for configuration directory
    config_dir_input = input(f"Configuration directory [{default_config_dir}]: ").strip()
    if not config_dir_input:
        config_dir = default_config_dir
    else:
        config_dir = Path(config_dir_input)
    
    # Client secrets and token files are always in CONFIG_DIR
    client_secrets_path = str(config_dir / "client_secrets.json")
    token_path = str(config_dir / "token.json")
    
    transcript_lang = input("Default raw transcript language [en]: ").strip()
    if not transcript_lang:
        transcript_lang = "en"
    
    upload_dir_input = input(f"Upload state directory [{default_upload_dir}]: ").strip()
    if not upload_dir_input:
        upload_dir = str(default_upload_dir)
    else:
        upload_dir = upload_dir_input
    
    gemini_key = input("Gemini API key (optional, press Enter to skip): ").strip()
    
    gemini_model = input("Gemini model [gemini-2.5-flash]: ").strip()
    if not gemini_model:
        gemini_model = "gemini-2.5-flash"
    
    # Create directories
    print("\nCreating directories...")
    directories_to_create = set()
    
    # Add config directory if needed
    
    client_secrets_dir = Path(client_secrets_path).parent
    token_dir = Path(token_path).parent
    directories_to_create.add(client_secrets_dir)
    directories_to_create.add(token_dir)
    # Don't create upload directory during configuration - it will be created on demand
    
    for directory in directories_to_create:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created {directory}")
        except Exception as e:
            print(f"✗ Failed to create {directory}: {e}")
    
    # Write .env file
    print("\nWriting configuration to .env...")
    env_content = f"""# PMIND Youtube MCP Configuration

# Configuration directory
CONFIG_DIR={config_dir}

# Default language for raw transcripts
YOUTUBE_RAW_TRANSCRIPT_LANG={transcript_lang}

# Directory for upload state files
YOUTUBE_UPLOAD_STATE_DIR={upload_dir}
"""
    
    if gemini_key:
        env_content += f"""
# Gemini AI configuration
GEMINI_API_KEY={gemini_key}
GEMINI_MODEL={gemini_model}
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✓ Configuration saved to .env")
    except Exception as e:
        print(f"✗ Failed to write .env file: {e}")
        sys.exit(1)
    
    # Ask if user wants to paste client credentials now
    print("\n" + "=" * 40)
    paste_prompt = f"\nDo you want to paste your OAuth client credentials JSON from Google Cloud Console? It will be saved to: {client_secrets_path} [y/N]: "
    paste_now = input(paste_prompt).strip().lower()
    
    if paste_now == 'y':
        print("\nPaste the OAuth 2.0 client credentials JSON from Google Cloud Console")
        print("(This is the file you downloaded in Step 3 of the README)")
        print("\nIMPORTANT: Paste the entire JSON in one go - do not break lines!")
        print("Press Enter twice when done:")
        print("Tip: In most terminals, you can paste with Ctrl+Shift+V or right-click")
        print("-" * 40)
        
        json_lines = []
        empty_line_count = 0
        
        while True:
            line = input()
            if line == "":
                empty_line_count += 1
                if empty_line_count >= 2:
                    break
            else:
                empty_line_count = 0
                json_lines.append(line)
        
        json_content = "\n".join(json_lines)
        
        try:
            # Write the client secrets file directly (no validation)
            with open(client_secrets_path, "w") as f:
                f.write(json_content)
            print(f"\n✓ Client secrets saved to: {client_secrets_path}")
            
            # Final instructions
            print("\n" + "=" * 40)
            print("\nConfiguration complete! Next step:")
            print("Run: uv run pmind-youtube-mcp --auth")
            show_manual_instructions = False
        except Exception as e:
            print(f"\n✗ Failed to save client secrets: {e}")
            show_manual_instructions = True
    else:
        show_manual_instructions = True
    
    if paste_now != 'y' or 'show_manual_instructions' in locals() and show_manual_instructions:
        # Show manual instructions
        print("\nNext steps:")
        print("1. Download OAuth client secrets from Google Cloud Console")
        print(f"2. Save as: {client_secrets_path}")
        print("3. Run: uv run pmind-youtube-mcp --auth")
        print("\nFor detailed instructions, see Step 3 in the README.")
    

def authenticate_only():
    """Perform authentication only and exit"""
    try:
        # Load configuration
        logger.info("Loading configuration for authentication...")
        config = Config.from_env()
        
        # Create YouTube client - this will trigger OAuth if needed
        logger.info("Initializing YouTube client for authentication...")
        youtube_client = YouTubeClient(
            client_secrets_file=config.client_secrets_file,
            token_file=config.token_file
        )
        
        # Test the authentication by making a simple API call
        logger.info("Testing authentication...")
        youtube_client.youtube.channels().list(part="id", mine=True).execute()
        
        logger.info(f"Authentication successful! Token saved to: {config.token_file}")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='PMIND MCP Youtube Server')
    parser.add_argument('--auth', action='store_true',
                       help='Authenticate only and exit (useful for setup)')
    parser.add_argument('--configure', action='store_true',
                       help='Run interactive configuration wizard')
    args = parser.parse_args()
    
    if args.configure:
        configure_interactive()
    elif args.auth:
        authenticate_only()
    else:
        try:
            mcp = create_server()
            mcp.run()
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()