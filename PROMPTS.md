# PMIND YouTube MCP Example Prompts

This document contains comprehensive example prompts for all YouTube MCP server functionality. Use these examples to explore the capabilities and understand how to interact with the server.

## 🎥 Video Operations

### Basic Video Queries
```
- "Get details for video dQw4w9WgXcQ"
- "Show me the most popular videos in the US right now"
- "List the top 10 trending videos in gaming category"
- "Find videos I've liked"
- "Get video statistics for https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

### Video Management (Requires OAuth)
```
- "Like video dQw4w9WgXcQ"
- "Remove my rating from video jNQXAC9IVRw"
- "Update my video abc123 title to 'My New Tutorial 2024'"
- "Change video xyz789 privacy to unlisted"
- "Add tags python, programming, tutorial to video abc123"
- "Report video xyz789 for spam content with comment 'misleading title'"
```

### Video Upload Examples
```
- "Upload video from /path/to/video.mp4 with title 'Test Upload' as private"
- "Start uploading /home/user/tutorial.mp4 with title 'Python Tutorial' and tags python, coding"
- "Check status of upload session upload_96239e09_1752279243"
- "Show all my active video uploads"
- "Cancel upload session upload_96239e09_1752279243"
- "List all my video uploads including completed ones"
```

## 🔍 Search Operations

### Basic Search
```
- "Search for Python programming tutorials"
- "Find videos about machine learning published after 2024-01-01"
- "Search for 4K nature videos"
- "Find live streams about gaming"
- "Search for Creative Commons licensed educational videos"
```

### Advanced Search
```
- "Search for short videos (under 4 minutes) about cooking in French"
- "Find HD videos about space within 50km of coordinates 37.7749,-122.4194"
- "Search for movie trailers sorted by view count"
- "Find upcoming live events about technology"
- "Search channels about fitness with over 100k subscribers"
```

## 📺 Channel Operations

### Channel Information
```
- "Get my YouTube channel information"
- "Show channel details for @mkbhd"
- "Get statistics for channel UC_x5XG1OV2P6uZZ5FSM9Ttw"
- "List videos from channel UCddiUEpeqJcYeBxX1IVBKvQ"
- "Show the latest 20 videos from channel UC_x5XG1OV2P6uZZ5FSM9Ttw"
```

### Channel Management
```
- "Update my channel description to 'Tech tutorials and reviews'"
- "List channels I manage"
- "Get my channel's branding settings"
```

## 📋 Playlist Operations

### Playlist Queries
```
- "Get information about playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
- "List videos in playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
- "Show my playlists"
- "Create a playlist called 'My Favorites' with description 'Best videos'"
```

### Playlist Management (Requires OAuth)
```
- "Add video dQw4w9WgXcQ to playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
- "Remove video from playlist at position 5"
- "Update playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf title to 'Updated Playlist'"
- "Delete playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
```

## 🔔 Subscription Operations

### View Subscriptions
```
- "Show my YouTube subscriptions"
- "List channels I'm subscribed to"
- "Check if I'm subscribed to channel UC_x5XG1OV2P6uZZ5FSM9Ttw"
- "Show my recent subscribers"
```

### Manage Subscriptions (Requires OAuth)
```
- "Subscribe to channel UC_x5XG1OV2P6uZZ5FSM9Ttw"
- "Unsubscribe from subscription SUB123456"
```

## 💬 Comments Operations

### Reading Comments
```
- "List comments on video dQw4w9WgXcQ"
- "Show top 20 comments on video jNQXAC9IVRw"
- "Get replies to comment COMMENT123"
- "List my recent comments"
```

### Writing Comments (Requires OAuth)
```
- "Comment 'Great tutorial, very helpful!' on video dQw4w9WgXcQ"
- "Reply 'Thanks for the feedback!' to comment COMMENT123"
- "Update comment COMMENT456 to say 'Updated: Great content!'"
- "Delete comment COMMENT789"
```

### Comment Moderation (Requires OAuth + Channel Owner)
```
- "Hold comment COMMENT123 for review"
- "Approve held comment COMMENT456"
- "Reject spam comment COMMENT789 and ban the author"
```

## 📝 Captions Operations

### Caption Queries
```
- "List available captions for video dQw4w9WgXcQ"
- "Download English captions for video jNQXAC9IVRw in SRT format"
- "Get Spanish captions for video abc123"
```

### Caption Management (Requires OAuth + Video Owner)
```
- "Delete caption track CAP123"
- "Update caption track CAP456 to published status"
```

## 🎨 Media Operations

### Thumbnails (Requires OAuth + Video Owner)
```
- "Set thumbnail for video dQw4w9WgXcQ from /path/to/thumbnail.jpg"
- "Upload custom thumbnail for video abc123"
```

### Watermarks (Requires OAuth + Channel Owner)
```
- "Set channel watermark from /path/to/watermark.png in bottom right corner"
- "Add watermark that appears after 10 seconds for 30 seconds"
- "Remove channel watermark"
```

## 📊 Metadata Operations

```
- "List video categories available in the US"
- "Show YouTube categories for Japan"
- "List all supported YouTube regions"
- "Show available YouTube interface languages"
- "Get UI languages with Spanish translations"
```

## 🤖 AI Analysis (Gemini)

### Video Analysis
```
- "Analyze https://www.youtube.com/watch?v=dQw4w9WgXcQ and summarize the key points"
- "What are the main topics discussed in https://youtube.com/watch?v=abc123"
- "Extract tutorial steps from https://www.youtube.com/watch?v=xyz789"
- "Identify technical concepts explained in this video: https://youtube.com/watch?v=123abc"
```

### Video Comparison
```
- "Compare these 3 tutorial videos and identify which explains the concept best: [url1, url2, url3]"
- "What are the differences between these two reviews: [url1, url2]"
- "Find common themes across these videos: [url1, url2, url3]"
```

### Video Q&A
```
- "Ask these questions about https://youtube.com/watch?v=abc123: 1) What tools are used? 2) What's the main topic? 3) Who is presenting?"
- "Get timestamps for when Python is mentioned in https://youtube.com/watch?v=xyz789"
- "Fact-check the claims made in this video: https://youtube.com/watch?v=123abc"
```

### AI Transcripts
```
- "Generate an AI transcript for https://youtube.com/watch?v=dQw4w9WgXcQ with timestamps"
- "Create an SRT subtitle file for https://youtube.com/watch?v=abc123 using AI"
- "Generate a transcript with visual descriptions for https://youtube.com/watch?v=xyz789"
```

## 📝 Raw Transcripts

```
- "Get the transcript for video dQw4w9WgXcQ"
- "Extract Spanish subtitles for video abc123"
- "Download existing YouTube captions for video xyz789"
- "Get auto-generated transcript for video jNQXAC9IVRw"
```
