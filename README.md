# AI Image MCP Server

A Model Context Protocol (MCP) server for AI-powered image analysis using OpenAI's Vision API.

## System Requirements

**Tested on:**
- macOS 14.3.0 (Darwin 23.3.0, ARM64)
- Python 3.13.0
- uv 0.7.13
- OpenAI API access

## Features

- Detailed image descriptions using GPT-4 Vision
- Targeted analysis (objects, text, colors, composition, emotions)
- Image comparison and similarity detection
- Technical metadata extraction
- Smart caching for performance and cost efficiency
- Support for PNG, JPEG, GIF, WebP formats

## MCP Tools

1. `describe_image(image_path, prompt)` - Get detailed image descriptions
2. `analyze_image_content(image_path, analysis_type)` - Analyze specific aspects
3. `compare_images(image1_path, image2_path, comparison_focus)` - Compare two images
4. `get_image_metadata(image_path)` - Extract technical metadata
5. `get_cache_info()` - View cache statistics
6. `clear_image_cache()` - Clear cached results

## Installation

```bash
# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup project
uv sync

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## Running the Server

```bash
uv run main.py
```

## MCP Integration

### Claude Desktop

```json
{
  "mcpServers": {
    "ai-image-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/ai-image-mcp",
        "run",
        "main.py"
      ],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cursor

Configure MCP in Cursor settings:

```json
{
  "servers": {
    "ai-image-mcp": {
      "command": "uv",
      "args": ["run", "main.py"],
      "cwd": "/absolute/path/to/ai-image-mcp",
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Analysis Types

- `general`: Overall image description
- `objects`: Object detection and identification
- `text`: Text extraction and OCR
- `colors`: Color analysis and palette
- `composition`: Visual composition and layout
- `emotions`: Emotional content and mood

## Project Structure

```
ai-image-mcp/
├── test_data/      # Sample images (gitignored)
├── tools/          # MCP tool definitions
├── utils/          # Utilities (caching, OpenAI client)
├── main.py         # Server entry point
└── server.py       # MCP server instance
```

## Caching

- Automatic file change detection via SHA-256 hashes
- 30-day cache expiration
- Separate cache entries for different prompts/analysis types
- Significant performance improvements (1000x+ faster than API calls)
