# PMIND YouTube MCP Server

> ⚠️ **Experimental**: This MCP server is in an experimental state and may have rough edges. Please report any issues you encounter.

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
- **📸 Screenshots**: Capture frames from videos at specific timestamps

### ✨ Key Features

- **🔐 OAuth Authentication**: Full YouTube API access with secure authentication
- **🚀 Background Video Uploads**: Video uploads spawn separate processes for non-blocking operation. Upload progress is tracked persistently, enabling you to start uploads and monitor them asynchronously
- **📡 Comprehensive YouTube API Coverage**: Complete implementation of YouTube Data API v3 - videos, channels, playlists, comments, captions, subscriptions, and more
- **🧠 AI-Powered Video Analysis**: Gemini integration for video content analysis, Q&A, and transcript generation
- **📄 Raw Transcript Support**: Extract existing YouTube transcripts via youtube-transcript-api without API quota usage
- **📸 Video Screenshots**: Extract frames at specific timestamps without API quota usage

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

Required:
- `CONFIG_DIR`: Configuration directory path
- `YOUTUBE_UPLOAD_STATE_DIR`: Directory for upload state files
- `YOUTUBE_RAW_TRANSCRIPT_LANG`: Default language for raw transcripts
- `GEMINI_MODEL`: Gemini model to use

Optional:
- `GEMINI_API_KEY`: API key for Gemini AI integration (only required if using Gemini tools)
- `YOUTUBE_SCREENSHOT_DEFAULT_QUALITY`: Default video quality for screenshots (144p, 240p, 360p, 480p, 720p, 1080p, best) - defaults to 1080p

## Usage

Once configured, you can start using the YouTube MCP server through your client. The server will automatically start when your client connects.

### Tool Reference
For a complete list of all tools with detailed parameters and examples, see [TOOLS.md](TOOLS.md).

### Example Prompts

For comprehensive examples of how to use each tool, see [PROMPTS.md](PROMPTS.md).

### Authentication Management

To re-authenticate or update credentials:

```bash
uv run pmind-youtube-mcp --auth
```

### Manual Server Testing

To test the server manually:

```bash
# Run the MCP server
uv run pmind-youtube-mcp
```