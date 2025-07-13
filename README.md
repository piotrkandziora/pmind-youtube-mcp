# PMIND YouTube MCP Server

> ⚠️ **Alpha Software**: This MCP server is in early alpha stage and may have rough edges. Please report any issues you encounter.

A Python implementation of the YouTube MCP (Model Context Protocol) server using FastMCP. This server provides comprehensive tools to interact with YouTube Data API v3, fetch video transcripts, and analyze content with Gemini AI integration.

## 🎯 Features

This MCP server provides comprehensive access to YouTube Data API v3 with additional AI-powered capabilities through Gemini integration.

### 📦 Core Capabilities

- **🎬 Video Management**: List, rate, update, delete videos, and manage uploads
- **🔍 Search**: Full YouTube search with advanced filters
- **📺 Channel Operations**: Manage channel content, banners, and sections
- **📋 Playlists**: Create and manage playlists and their items
- **🔔 Subscriptions**: Manage channel subscriptions
- **💬 Comments**: Read and write comments with moderation
- **📝 Captions**: Access and manage video captions
- **🎨 Media**: Upload thumbnails and manage watermarks
- **📊 Metadata**: Access categories, regions, and languages
- **🤖 AI Analysis**: Analyze videos with Gemini AI

### ✨ Key Features

- **🔐 OAuth Authentication**: Full YouTube API access with secure authentication
- **🚀 Background Video Uploads**: Video uploads spawn separate processes for non-blocking operation. Upload progress is tracked persistently, enabling you to start uploads and monitor them asynchronously
- **📡 Comprehensive YouTube API Coverage**: Complete implementation of YouTube Data API v3 - videos, channels, playlists, comments, captions, subscriptions, and more
- **🧠 AI-Powered Video Analysis**: Gemini integration for video content analysis, Q&A, and transcript generation
- **📄 Raw Transcript Support**: Extract existing YouTube transcripts via youtube-transcript-api without API quota usage

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/raveenplgithub/pmind-mcp-youtube.git
cd pmind-youtube-mcp
```

### Step 2: Install Dependencies

```bash
# Install dependencies using uv
uv sync
```

### Step 3: Set Up Google OAuth Credentials

#### Access Google Cloud Console
- Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
- Sign in with your Google account

#### Create or Select Project
- Click the project dropdown at the top
- Either select existing or click "NEW PROJECT"
- Enter project name (e.g., "YouTube MCP Server")
- Click "CREATE"

#### Enable YouTube Data API v3
- In left sidebar: **APIs & Services** → **Library**
- Search for "YouTube Data API v3"
- Click on it and press **ENABLE**

#### Configure OAuth Consent Screen (First time only)
- Go to **APIs & Services** → **OAuth consent screen**
- Choose **External** and click **CREATE**
- Fill required fields:
  - App name: "YouTube MCP Server"
  - User support email: Your email
  - Developer contact: Your email
- Click **SAVE AND CONTINUE**
- On Scopes page, click **ADD OR REMOVE SCOPES**
- Select these scopes:
  - `https://www.googleapis.com/auth/youtube`
  - `https://www.googleapis.com/auth/youtube.force-ssl`
- Click **UPDATE** → **SAVE AND CONTINUE**
- **IMPORTANT for Testing**: On the Test users page, click **+ ADD USERS**
  - Add your Google account email address
  - Add any other email addresses that will use the app during testing
  - Click **ADD** → **SAVE AND CONTINUE**
- Review the summary and click **BACK TO DASHBOARD**

**Note**: Keep your app in **Testing** mode for personal use - no verification needed. Just add your email as a test user.

#### Create OAuth 2.0 Credentials
- Go to **APIs & Services** → **Credentials**
- Click **+ CREATE CREDENTIALS** → **OAuth client ID**
- Select **Desktop app** as Application type
- Name it (e.g., "YouTube MCP Desktop Client")
- Click **CREATE**

#### Download Credentials
- Click **DOWNLOAD JSON** button in the popup
- Save the file for use in Step 4

### Step 4: Configure the Server

Run the configuration wizard:

```bash
uv run pmind-youtube-mcp --configure
```

This will:
- Prompt you for all configuration values
- Create necessary directories
- Generate the `.env` file automatically
- Optionally let you paste your client credentials JSON directly
- Show you where to place your client secrets file

If you didn't paste the credentials during configuration, you'll need to manually copy the downloaded file to `~/.pmind-youtube-mcp/client_secrets.json`.

### Step 5: Authenticate

Run the authentication command to set up OAuth:

```bash
uv run pmind-youtube-mcp --auth
```

This will:
- Open your browser for Google OAuth login
- Ask you to grant permissions for YouTube access
- Save the authentication token to `~/.pmind-youtube-mcp/token.json`

### Step 6: Configure with Your Client

Add the MCP server to your client's MCP configuration:

```json
{
  "mcpServers": {
    "pmind-youtube": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/pmind-youtube-mcp", "pmind-youtube-mcp"]
    }
  }
}
```

Replace `/path/to/pmind-youtube-mcp` with the actual path where you cloned the repository.

#### For Claude Code (CLI)

Use the following command to add the server:

```bash
claude mcp add pmind-youtube-mcp -- uv run --directory /path/to/pmind-youtube-mcp pmind-youtube-mcp
```

## Configuration Options

### Environment Variables

- `CONFIG_DIR`: Override the default configuration directory (default: `~/.pmind-youtube-mcp`)
- `YOUTUBE_RAW_TRANSCRIPT_LANG`: Default language for raw transcripts (default: 'en')
- `YOUTUBE_UPLOAD_STATE_DIR`: Directory for upload state files (default: '/tmp/pmind-youtube-mcp-uploads')
- `GEMINI_API_KEY`: API key for Gemini AI integration
- `GEMINI_MODEL`: Gemini model to use (default: 'gemini-2.5-flash')

## Usage

Once configured, you can start using the YouTube MCP server through your client. The server will automatically start when your client connects.

### Example Prompts

For comprehensive examples of how to use each tool, see [PROMPTS.md](PROMPTS.md).

### Manual Server Testing

To test the server manually:

```bash
# Run the MCP server
uv run pmind-youtube-mcp
```

### Authentication Management

To re-authenticate or update credentials:

```bash
uv run pmind-youtube-mcp --auth
```

## Tool Reference

For a complete list of all 63 available tools with detailed parameters and examples, see [TOOLS.md](TOOLS.md).

### Understanding YouTube IDs

- **Video ID**: The part after `v=` in URLs like `youtube.com/watch?v=dQw4w9WgXcQ`
- **Channel ID**: Usually starts with `UC` and is 24 characters long
- **Playlist ID**: Usually starts with `PL` or `UU` and is 34 characters long

### Common Use Cases

1. **Research and Analysis**
   - Search for videos on a topic and analyze their metadata
   - Compare view counts and engagement across videos
   - Study channel growth by examining video publication dates

2. **Content Discovery**
   - Find popular videos in a niche
   - Explore channels with specific content
   - Browse curated playlists

3. **Transcript Analysis**
   - Extract transcripts for accessibility
   - Analyze video content without watching
   - Translate content using transcripts

4. **Channel Monitoring**
   - Track new uploads from specific channels
   - Monitor channel statistics
   - Analyze upload patterns

### Error Handling

The server will return error messages for common issues:
- **"API quota exceeded"**: You've hit the daily limit
- **"Resource not found"**: Invalid video/channel/playlist ID
- **"Invalid request parameters"**: Check your input format
- **"Transcripts are disabled"**: Video doesn't allow transcripts

## API Quota Management

The YouTube Data API has quota limits. This server tracks quota usage:

**Read Operations (1 unit):**
- Videos.list, Channels.list, Playlists.list
- PlaylistItems.list, Comments.list, CommentThreads.list
- Captions.list, ChannelSections.list, Members.list
- MembershipsLevels.list, VideoCategories.list
- i18nRegions.list, i18nLanguages.list

**Search Operations (100 units):**
- Search.list

**Write Operations (50 units):**
- Insert, Update, Delete operations for most resources
- Videos.rate, Videos.reportAbuse
- Comments.setModerationStatus
- Watermarks.set, Watermarks.unset

**Special Operations:**
- Captions.download: No quota cost (direct download)
- Thumbnails.set: 50 units (requires file upload)
- ChannelBanners.insert: 50 units (requires file upload)

Default quota is 10,000 units per day.



