import os
import base64
from pathlib import Path
from openai import OpenAI
import requests
from PIL import Image

def get_openai_client() -> OpenAI:
    """Get OpenAI client with API key from environment."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI(api_key=api_key)

def encode_image_to_base64(image_path: Path) -> str:
    """Encode image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def is_valid_image_format(file_path: Path) -> bool:
    """Check if file is a valid image format supported by OpenAI Vision."""
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    return file_path.suffix.lower() in valid_extensions

def get_image_info(image_path: Path) -> dict:
    """Get basic image information."""
    try:
        with Image.open(image_path) as img:
            return {
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "file_size": image_path.stat().st_size
            }
    except Exception as e:
        return {"error": str(e)} 