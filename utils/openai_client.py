import os
import base64
from pathlib import Path
from openai import OpenAI
import requests
from PIL import Image
from typing import Dict, List, Optional, Union
import json
import time
import io

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

def save_base64_image(base64_data: str, output_path: Path, image_format: str = "PNG") -> bool:
    """Save base64 encoded image data to file."""
    try:
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Open and save the image
        with Image.open(io.BytesIO(image_data)) as img:
            img.save(output_path, format=image_format)
        
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

def download_image_from_url(url: str, output_path: Path, timeout: int = 30) -> bool:
    """Download image from URL and save to file."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"Error downloading image: {e}")
        return False

def validate_image_generation_params(model: str, size: Optional[str] = None, quality: Optional[str] = None,
                                   style: Optional[str] = None, response_format: Optional[str] = None,
                                   n: Optional[int] = None) -> Dict[str, str]:
    """Validate and normalize image generation parameters."""
    errors = []
    
    # Validate model
    valid_models = {"dall-e-2", "dall-e-3", "gpt-image-1"}
    if model not in valid_models:
        errors.append(f"Invalid model '{model}'. Must be one of: {', '.join(valid_models)}")
    
    # Validate size based on model
    if size:
        valid_sizes = {
            "dall-e-2": {"256x256", "512x512", "1024x1024"},
            "dall-e-3": {"1024x1024", "1792x1024", "1024x1792"},
            "gpt-image-1": {"1024x1024", "1536x1024", "1024x1536", "auto"}
        }
        if model in valid_sizes and size not in valid_sizes[model]:
            errors.append(f"Invalid size '{size}' for model '{model}'. Valid sizes: {', '.join(valid_sizes[model])}")
    
    # Validate quality based on model
    if quality:
        valid_quality = {
            "dall-e-2": {"standard"},
            "dall-e-3": {"standard", "hd"},
            "gpt-image-1": {"auto", "high", "medium", "low"}
        }
        if model in valid_quality and quality not in valid_quality[model]:
            errors.append(f"Invalid quality '{quality}' for model '{model}'. Valid quality: {', '.join(valid_quality[model])}")
    
    # Validate style (only for dall-e-3)
    if style and model != "dall-e-3":
        errors.append(f"Style parameter is only supported for dall-e-3, not '{model}'")
    elif style and style not in {"vivid", "natural"}:
        errors.append(f"Invalid style '{style}'. Must be 'vivid' or 'natural'")
    
    # Validate response_format
    if response_format:
        if model == "gpt-image-1":
            errors.append("response_format is not supported for gpt-image-1 (always returns base64)")
        elif response_format not in {"url", "b64_json"}:
            errors.append(f"Invalid response_format '{response_format}'. Must be 'url' or 'b64_json'")
    
    # Validate n (number of images)
    if n is not None:
        if n < 1 or n > 10:
            errors.append(f"Invalid n '{n}'. Must be between 1 and 10")
        if model == "dall-e-3" and n != 1:
            errors.append("dall-e-3 only supports n=1")
    
    return {"errors": errors} if errors else {"valid": True}

def prepare_image_for_upload(image_path: Path, model: str) -> Optional[bytes]:
    """Prepare image file for upload based on model requirements."""
    try:
        # Check file size limits
        max_sizes = {
            "dall-e-2": 4 * 1024 * 1024,  # 4MB
            "gpt-image-1": 50 * 1024 * 1024  # 50MB
        }
        
        file_size = image_path.stat().st_size
        if model in max_sizes and file_size > max_sizes[model]:
            raise ValueError(f"Image too large for {model}: {file_size} bytes (max: {max_sizes[model]} bytes)")
        
        # For dall-e-2, ensure image is square PNG
        if model == "dall-e-2":
            with Image.open(image_path) as img:
                if img.size[0] != img.size[1]:
                    raise ValueError("dall-e-2 requires square images")
                if img.format != "PNG":
                    # Convert to PNG
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    return buffer.getvalue()
        
        # Return file bytes
        with open(image_path, "rb") as f:
            return f.read()
    
    except Exception as e:
        print(f"Error preparing image: {e}")
        return None 