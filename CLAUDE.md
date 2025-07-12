# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
```bash
# Install dependencies
poetry install

# Install in development mode with extras
poetry install --with dev
```

### Running the Server
```bash
# Run with Poetry
poetry run pmind-youtube-mcp

# Or activate shell and run directly
poetry shell
pmind-youtube-mcp
```

### Code Quality
```bash
# Format code
poetry run black src/

# Lint code
poetry run ruff check src/
```

## Architecture Overview

This is a comprehensive YouTube MCP (Model Context Protocol) server built with FastMCP, providing tools to interact with all YouTube Data API v3 endpoints. The architecture follows a modular service-based design with complete API coverage:

### Core Components

1. **Server Entry Point** (`src/server.py`)
   - Creates and configures the FastMCP server instance
   - Registers all service modules
   - Stores configuration in server state for tool access
   - Single shared YouTube client instance for all services

2. **Configuration** (`src/config.py`)
   - Pydantic-based configuration model
   - Loads from environment variables (supports .env files)
   - OAuth authentication only (no API key support)
   - Settings:
     - `CONFIG_DIR` (default: '~/.pmind-youtube-mcp') - contains client_secrets.json and token.json
     - `YOUTUBE_RAW_TRANSCRIPT_LANG` (default: 'en')
     - `YOUTUBE_UPLOAD_STATE_DIR` (default: '/tmp/pmind-youtube-mcp-uploads')
     - `GEMINI_API_KEY` (optional) - API key for Gemini AI integration
     - `GEMINI_MODEL` (default: 'gemini-2.5-flash') - Gemini model to use

3. **Service Modules** (`src/services/`)
   - Each module registers related tools with the MCP server
   - Tools are decorated with `@mcp.tool` for automatic registration
   - All tools are async and return structured data
   - Error handling returns error objects instead of raising exceptions
   
   **Complete service list:**
   - **Core resources**: videos, channels, playlists, search
   - **User interaction**: subscriptions, comments, comment_threads
   - **Media management**: captions, thumbnails, watermarks, channel_banners
   - **Channel features**: channel_sections, members, memberships_levels
   - **Playlist management**: playlist_items, playlist_images
   - **Metadata**: video_categories, i18n_regions, i18n_languages
   - **External**: transcripts (no auth required)
   - **AI Integration**: gemini (YouTube video analysis with Gemini AI)

4. **YouTube Client** (`src/utils/youtube_client.py`)
   - Wrapper around Google's YouTube Data API client
   - OAuth 2.0 authentication with token persistence
   - Comprehensive error handling with specific error reasons
   - Quota tracking for all API operations
   - Async methods for all YouTube Data API v3 endpoints
   - Enhanced error parsing for all HTTP status codes (400, 401, 403, 404, 429, 500+)

### Tool Registration Pattern

Each service module follows the same pattern:
```python
def register_tools(mcp: FastMCP, config: Config, youtube_client: YouTubeClient):
    # YouTube client is now passed in from server.py (single shared instance)
    
    @mcp.tool
    async def tool_name(params...) -> Dict[str, Any]:
        # Tool implementation
```

### Key Design Decisions

1. **OAuth-Only Authentication**: Uses OAuth 2.0 for all API access (no API key support)
2. **FastMCP Framework**: Uses FastMCP for simplified MCP server implementation
3. **Async-First**: All tools are async for better performance
4. **Service Modularity**: Each YouTube resource type has its own service module
5. **Error Resilience**: Tools return error dictionaries rather than raising exceptions
6. **Quota Awareness**: YouTube client tracks API quota usage  
7. **Token Persistence**: OAuth tokens are saved to disk for reuse across sessions
8. **Comprehensive API Coverage**: Implements all major YouTube Data API v3 endpoints
9. **Single Client Instance**: One shared YouTube client to reduce OAuth token checks
10. **Consistent Tool Naming**: All tools follow resource_action pattern (e.g., videos_list)

### API Integration

- Uses `google-api-python-client` for YouTube Data API v3
- Uses `youtube-transcript-api` for fetching video transcripts without API key
- All API responses are formatted consistently with relevant fields extracted
- File upload operations (thumbnails, banners, watermarks) return NotImplementedError
  - These would require `googleapiclient.http.MediaFileUpload` implementation

### API Documentation Reference

For detailed YouTube API documentation, refer to: https://developers.google.com/youtube/v3/docs/

This is the authoritative source for:
- API endpoint specifications
- Parameter definitions and requirements
- Response formats
- Quota costs
- Best practices and usage limits

### Complete API Coverage

This implementation covers all major YouTube Data API v3 resources:

**Fully Implemented:**
- Videos (list, getRating, rate, update, delete, reportAbuse)
- Channels (list, update)
- Playlists (list, insert, update, delete)
- PlaylistItems (list, insert, update, delete)
- Search (comprehensive search with all parameters)
- Subscriptions (list, insert, delete)
- Comments (list, insert, update, delete, setModerationStatus)
- CommentThreads (list, insert)
- Captions (list, download, update, delete)
- ChannelSections (list, insert, update, delete)
- Members (list)
- MembershipsLevels (list)
- VideoCategories (list)
- i18nRegions (list)
- i18nLanguages (list)

**Partially Implemented (file upload limitation):**
- Thumbnails (set - requires file upload)
- ChannelBanners (insert - requires file upload)
- Watermarks (set, unset - set requires file upload)

**Not Implemented:**
- Activities API (deprecated)
- GuideCategories API (limited use case)
- LiveBroadcasts/LiveStreams API (specialized use case)