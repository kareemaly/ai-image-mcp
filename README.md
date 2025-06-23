# AI Image MCP Server

A comprehensive Model Context Protocol (MCP) server that provides both **AI-powered image analysis** and **AI image generation** capabilities using OpenAI's Vision API and image generation models.

## System Requirements

**Tested on:**
- macOS 14.3.0 (Darwin 23.3.0, ARM64)
- Python 3.13.0
- uv 0.7.13
- OpenAI API access

## Features

### 🔍 Image Analysis & Description
- **Smart Image Analysis**: Analyze images using OpenAI's GPT-4O Vision model
- **Targeted Analysis**: Analyze specific aspects (objects, text, colors, composition, emotions)
- **Image Comparisons**: Compare two images and highlight similarities/differences
- **Metadata Extraction**: Get technical information about image files
- **Intelligent Caching**: Cache analysis results to avoid repeated API calls
- **Multiple Formats**: Support for PNG, JPEG, GIF, and WebP formats

### 🎨 Image Generation & Editing
- **Text-to-Image Generation**: Create images from text prompts using DALL-E 2, DALL-E 3, or GPT-Image-1
- **Image Editing**: Edit existing images with text prompts using GPT-Image-1 or DALL-E 2
- **Image Variations**: Create variations of existing images using DALL-E 2
- **Flexible Output**: Save generated images locally with custom naming and directories
- **Model Support**: Full support for all OpenAI image generation models with their specific features

## MCP Tools

1. `describe_image(image_path, prompt)` - Get detailed image descriptions
2. `analyze_image_content(image_path, analysis_type)` - Analyze specific aspects
3. `compare_images(image1_path, image2_path, comparison_focus)` - Compare two images
4. `get_image_metadata(image_path)` - Extract technical metadata
5. `get_cache_info()` - View cache statistics
6. `clear_image_cache()` - Clear cached results

## Installation

1. Install dependencies:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv add mcp[cli] openai pillow requests
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Run the server:
```bash
uv run main.py
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

## Available Tools

### Image Analysis Tools

#### `describe_image`
Analyze an image and provide a detailed description.
- **Parameters**: 
  - `image_path` (str): Path to the image file
  - `prompt` (str, optional): Custom analysis prompt
- **Supports**: PNG, JPEG, GIF, WebP
- **Features**: Caching, file validation, comprehensive error handling

#### `analyze_image_content`
Perform targeted analysis of specific image aspects.
- **Parameters**:
  - `image_path` (str): Path to the image file
  - `analysis_type` (str): Type of analysis - "general", "objects", "text", "colors", "composition", "emotions"
- **Features**: Specialized prompts for different analysis types

#### `compare_images`
Compare two images and highlight similarities and differences.
- **Parameters**:
  - `image1_path` (str): Path to first image
  - `image2_path` (str): Path to second image
  - `comparison_focus` (str): What to focus on in comparison

#### `get_image_metadata`
Get technical metadata about an image file.
- **Returns**: File size, dimensions, format, color mode, aspect ratio, etc.

### Image Generation Tools

#### `generate_image`
Generate images from text prompts using OpenAI's image generation models.
- **Parameters**:
  - `prompt` (str): Text description of desired image
  - `model` (str): "dall-e-2", "dall-e-3", or "gpt-image-1" (default: dall-e-3)
  - `size` (str, optional): Image dimensions (varies by model)
  - `quality` (str, optional): Quality setting (varies by model)
  - `style` (str, optional): "vivid" or "natural" (DALL-E 3 only)
  - `n` (int, optional): Number of images (1-10, DALL-E 3 only supports 1)
  - `output_dir` (str): Directory to save images (default: "./generated_images")
  - `filename_prefix` (str): Prefix for filenames (default: "generated")

**Model-Specific Features**:
- **DALL-E 2**: Basic generation, sizes: 256x256, 512x512, 1024x1024
- **DALL-E 3**: High quality, styles (vivid/natural), sizes: 1024x1024, 1792x1024, 1024x1792
- **GPT-Image-1**: Advanced features, transparency support, compression control

#### `edit_image`
Edit existing images using text prompts.
- **Parameters**:
  - `image_path` (str): Path to image to edit
  - `prompt` (str): Description of desired edit
  - `mask_path` (str, optional): Path to mask image (PNG with transparent edit areas)
  - `model` (str): "gpt-image-1" or "dall-e-2" (default: gpt-image-1)
  - `size`, `quality`, `n`: Model-specific options
  - `output_dir`, `filename_prefix`: Output configuration

**Supported Models**: GPT-Image-1 (up to 16 images, 50MB each) and DALL-E 2 (1 square PNG, 4MB max)

#### `create_image_variations`
Create variations of existing images using DALL-E 2.
- **Parameters**:
  - `image_path` (str): Path to source image (must be square PNG, <4MB)
  - `n` (int): Number of variations (1-10, default: 2)
  - `size` (str): Variation size - "256x256", "512x512", "1024x1024"
  - `output_dir`, `filename_prefix`: Output configuration

#### `list_generated_images`
List all generated images in a directory with metadata.
- **Parameters**:
  - `directory` (str): Directory to scan (default: "./generated_images")
- **Returns**: File listing with sizes, dimensions, modification dates

### Cache Management Tools

#### `get_cache_info`
Get information about the analysis cache (file count, size, location).

#### `clear_image_cache`
Clear all cached analysis results.

## Model Comparison

| Feature | DALL-E 2 | DALL-E 3 | GPT-Image-1 |
|---------|----------|----------|-------------|
| **Generation** | ✅ Basic | ✅ High Quality | ✅ Advanced |
| **Editing** | ✅ Limited | ❌ | ✅ Advanced |
| **Variations** | ✅ | ❌ | ❌ |
| **Max Images** | 10 | 1 | 10 |
| **Sizes** | 256x256, 512x512, 1024x1024 | 1024x1024, 1792x1024, 1024x1792 | 1024x1024, 1536x1024, 1024x1536 |
| **Styles** | ❌ | vivid, natural | ❌ |
| **Quality** | standard | standard, hd | auto, high, medium, low |
| **Transparency** | ❌ | ❌ | ✅ |
| **Max Prompt** | 1000 chars | 4000 chars | 32000 chars |

## Usage Examples

### Generate a Basic Image
```python
# Generate an image with DALL-E 3
generate_image(
    prompt="A serene mountain landscape at sunset with a crystal clear lake",
    model="dall-e-3",
    size="1792x1024",
    quality="hd",
    style="natural"
)
```

### Edit an Existing Image
```python
# Add elements to an image
edit_image(
    image_path="./photos/room.png",
    prompt="Add a beautiful bookshelf filled with colorful books to the left wall",
    model="gpt-image-1",
    quality="high"
)
```

### Create Image Variations
```python
# Create variations of a logo
create_image_variations(
    image_path="./logos/logo.png",
    n=5,
    size="1024x1024"
)
```

### Analyze Generated Images
```python
# Analyze a generated image
describe_image(
    image_path="./generated_images/generated_1234567890_1.png",
    prompt="Describe the artistic style and composition of this generated image"
)
```

## File Organization

Generated images are automatically organized in separate directories:
- `./generated_images/` - Text-to-image generations
- `./edited_images/` - Image edits
- `./image_variations/` - Image variations

Files are named with timestamps to avoid conflicts:
- `generated_1234567890_1.png`
- `edited_1234567890_1.png`
- `variation_1234567890_1.png`

## Error Handling

The server includes comprehensive error handling for:
- Invalid image formats and file paths
- Model-specific parameter validation
- File size and dimension limits
- API quota and rate limiting
- Network connectivity issues
- Malformed prompts and parameters

## Cache System

The analysis tools use an intelligent caching system:
- **File Change Detection**: Uses SHA-256 hashes to detect file changes
- **30-Day Expiration**: Automatically expires old cache entries
- **Safe Operation**: Cache failures don't affect main functionality
- **Efficient Storage**: Uses MD5 hashes for safe cache key generation

## Requirements

- Python 3.13+
- OpenAI API key with access to Vision API and Image Generation
- Required packages: `mcp[cli]>=1.9.4`, `openai>=1.90.0`, `pillow>=11.2.1`, `requests>=2.32.4`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
