import os
from pathlib import Path
from typing import Optional, List
import time
from server import mcp
from utils.path_utils import resolve_path, validate_image_path
from utils.openai_client import (
    get_openai_client, 
    validate_image_generation_params,
    save_base64_image,
    download_image_from_url,
    prepare_image_for_upload,
    is_valid_image_format
)

@mcp.tool()
def generate_image(
    working_dir: str,
    prompt: str,
    model: str = "dall-e-3",
    size: Optional[str] = None,
    quality: Optional[str] = None,
    style: Optional[str] = None,
    n: int = 1,
    output_dir: str = "generated_images",
    filename_prefix: str = "generated"
) -> str:
    """
    Generate images from text prompts using OpenAI's image generation models.
    
    Args:
        working_dir: Absolute path to the working directory for file operations
        prompt: Text description of the desired image (max 32000 chars for gpt-image-1, 4000 for dall-e-3, 1000 for dall-e-2)
        model: Model to use - "dall-e-2", "dall-e-3", or "gpt-image-1" (default: dall-e-3)
        size: Image size - varies by model (e.g., "1024x1024", "1792x1024" for dall-e-3)
        quality: Quality setting - varies by model ("standard", "hd" for dall-e-3)
        style: Style for dall-e-3 - "vivid" or "natural" (default: vivid)
        n: Number of images to generate (1-10, dall-e-3 only supports 1)
        output_dir: Directory relative to working_dir to save generated images
        filename_prefix: Prefix for generated image filenames
    
    Returns:
        Information about the generated images and their file paths
    """
    try:
        # Validate working directory
        working_path = Path(working_dir)
        if not working_path.is_absolute():
            return f"Error: working_dir must be an absolute path, got: {working_dir}"
        if not working_path.exists():
            return f"Error: working_dir does not exist: {working_dir}"
        if not working_path.is_dir():
            return f"Error: working_dir is not a directory: {working_dir}"
        
        # Validate parameters
        validation = validate_image_generation_params(model, size, quality, style, n=n)
        if "errors" in validation:
            return f"Parameter validation errors:\n" + "\n".join(validation["errors"])
        
        # Validate prompt length
        max_prompt_lengths = {
            "dall-e-2": 1000,
            "dall-e-3": 4000,
            "gpt-image-1": 32000
        }
        if len(prompt) > max_prompt_lengths.get(model, 1000):
            return f"Error: Prompt too long for {model}. Maximum length: {max_prompt_lengths[model]} characters"
        
        # Create output directory relative to working directory
        output_path = working_path / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get OpenAI client
        client = get_openai_client()
        
        # Prepare request parameters
        params = {
            "model": model,
            "prompt": prompt,
            "n": n or 1
        }
        
        # Add optional parameters based on model
        if size:
            params["size"] = size
        if quality:
            params["quality"] = quality
        if style and model == "dall-e-3":
            params["style"] = style
        
        # Set response format based on model
        if model == "gpt-image-1":
            # gpt-image-1 always returns base64
            pass
        else:
            params["response_format"] = "b64_json"  # Use base64 for consistent handling
        
        # Generate images
        response = client.images.generate(**params)
        
        # Save generated images
        saved_files = []
        timestamp = int(time.time())
        
        for i, image_data in enumerate(response.data):
            # Generate filename
            filename = f"{filename_prefix}_{timestamp}_{i+1}.png"
            file_path = output_path / filename
            
            # Save image
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                # Base64 data
                if save_base64_image(image_data.b64_json, file_path):
                    saved_files.append(str(file_path))
                else:
                    return f"Error: Failed to save image {i+1}"
            elif hasattr(image_data, 'url') and image_data.url:
                # URL data (dall-e-2 and dall-e-3 with url response format)
                if download_image_from_url(image_data.url, file_path):
                    saved_files.append(str(file_path))
                else:
                    return f"Error: Failed to download image {i+1} from URL"
            else:
                return f"Error: No image data found in response for image {i+1}"
        
        # Format response
        result = f"Successfully generated {len(saved_files)} image(s) using {model}\n\n"
        result += f"Prompt: {prompt}\n"
        result += f"Parameters: model={model}"
        if size:
            result += f", size={size}"
        if quality:
            result += f", quality={quality}"
        if style:
            result += f", style={style}"
        result += f", n={n}\n\n"
        result += "Generated files:\n"
        
        for file_path in saved_files:
            result += f"- {file_path}\n"
        
        # Add usage information if available
        if hasattr(response, 'usage') and response.usage:
            result += f"\nToken usage: {response.usage.total_tokens} total tokens"
        
        return result
        
    except Exception as e:
        return f"Error generating image: {str(e)}"

@mcp.tool()
def edit_image(
    working_dir: str,
    image_path: str,
    prompt: str,
    mask_path: Optional[str] = None,
    model: str = "gpt-image-1",
    size: Optional[str] = None,
    quality: Optional[str] = None,
    n: int = 1,
    output_dir: str = "./edited_images",
    filename_prefix: str = "edited"
) -> str:
    """
    Edit or extend existing images using OpenAI's image editing capabilities.
    Supports gpt-image-1 and dall-e-2 models.
    
    Args:
        working_dir: Absolute path to the working directory for file operations
        image_path: Path to the image to edit relative to working_dir (PNG, WebP, JPG for gpt-image-1; PNG for dall-e-2)
        prompt: Description of the desired edit (max 32000 chars for gpt-image-1, 1000 for dall-e-2)
        mask_path: Optional path to mask image (PNG with transparent areas indicating edit regions)
        model: Model to use - "gpt-image-1" or "dall-e-2" (default: gpt-image-1)
        size: Output image size
        quality: Quality setting (gpt-image-1 only)
        n: Number of edited images to generate (1-10)
        output_dir: Directory relative to working_dir to save edited images
        filename_prefix: Prefix for edited image filenames
    
    Returns:
        Information about the edited images and their file paths
    """
    try:
        # Validate model (only gpt-image-1 and dall-e-2 support editing)
        if model not in {"gpt-image-1", "dall-e-2"}:
            return "Error: Image editing only supports 'gpt-image-1' and 'dall-e-2' models"
        
        # Validate parameters
        validation = validate_image_generation_params(model, size, quality, n=n)
        if "errors" in validation:
            return f"Parameter validation errors:\n" + "\n".join(validation["errors"])
        
        # Validate prompt length
        max_prompt_lengths = {
            "dall-e-2": 1000,
            "gpt-image-1": 32000
        }
        if len(prompt) > max_prompt_lengths.get(model, 1000):
            return f"Error: Prompt too long for {model}. Maximum length: {max_prompt_lengths[model]} characters"
        
        # Validate working directory
        working_path = Path(working_dir)
        if not working_path.is_absolute():
            return f"Error: working_dir must be an absolute path, got: {working_dir}"
        if not working_path.exists():
            return f"Error: working_dir does not exist: {working_dir}"
        if not working_path.is_dir():
            return f"Error: working_dir is not a directory: {working_dir}"
        
        # Validate image path with clear error messages
        is_valid, error_message, resolved_image_path = validate_image_path(image_path, "read", working_dir)
        if not is_valid:
            return error_message
        
        if not is_valid_image_format(resolved_image_path):
            return (
                f"Error: Unsupported image format.\n"
                f"• File: '{image_path}'\n"
                f"• Supported formats: PNG, JPEG, JPG, GIF, WebP\n"
                f"• Suggestion: Convert the image to a supported format or use a different image file."
            )
        
        # Prepare image for upload
        image_data = prepare_image_for_upload(resolved_image_path, model)
        if not image_data:
            return f"Error: Failed to prepare image for upload"
        
        # Handle mask if provided
        mask_data = None
        if mask_path:
            resolved_mask_path = resolve_path(mask_path, working_dir)
            if not resolved_mask_path.exists():
                return f"Error: Mask file '{mask_path}' not found"
            
            # Validate mask (must be PNG)
            if resolved_mask_path.suffix.lower() != '.png':
                return "Error: Mask must be a PNG file"
            
            with open(resolved_mask_path, 'rb') as f:
                mask_data = f.read()
        
        # Create output directory relative to working directory
        output_path = working_path / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get OpenAI client
        client = get_openai_client()
        
        # Prepare request
        files = {
            'image': image_data,
            'prompt': prompt,
            'model': model,
            'n': n or 1
        }
        
        if mask_data:
            files['mask'] = mask_data
        if size:
            files['size'] = size
        if quality and model == "gpt-image-1":
            files['quality'] = quality
        
        # Set response format
        if model == "dall-e-2":
            files['response_format'] = 'b64_json'
        
        # Make API call
        if model == "gpt-image-1":
            # For gpt-image-1, we need to format as multipart form data
            form_data = []
            form_data.append(('image', ('image.png', image_data, 'image/png')))
            if mask_data:
                form_data.append(('mask', ('mask.png', mask_data, 'image/png')))
            
            # Use requests directly for multipart form data
            import requests
            api_key = os.environ.get("OPENAI_API_KEY")
            headers = {"Authorization": f"Bearer {api_key}"}
            
            data = {
                'model': model,
                'prompt': prompt,
                'n': str(n)
            }
            if size:
                data['size'] = size
            if quality:
                data['quality'] = quality
            
            response = requests.post(
                "https://api.openai.com/v1/images/edits",
                headers=headers,
                files=form_data,
                data=data
            )
            response.raise_for_status()
            response_data = response.json()
        else:
            # Use OpenAI client for dall-e-2
            response = client.images.edit(
                image=image_data,
                prompt=prompt,
                mask=mask_data,
                model=model,
                n=n,
                size=size,
                response_format='b64_json'
            )
            response_data = response.model_dump()
        
        # Save edited images
        saved_files = []
        timestamp = int(time.time())
        
        for i, image_item in enumerate(response_data['data']):
            # Generate filename
            filename = f"{filename_prefix}_{timestamp}_{i+1}.png"
            file_path = output_path / filename
            
            # Save image
            if 'b64_json' in image_item:
                if save_base64_image(image_item['b64_json'], file_path):
                    saved_files.append(str(file_path))
                else:
                    return f"Error: Failed to save edited image {i+1}"
            elif 'url' in image_item:
                if download_image_from_url(image_item['url'], file_path):
                    saved_files.append(str(file_path))
                else:
                    return f"Error: Failed to download edited image {i+1}"
        
        # Format response
        result = f"Successfully edited image using {model}\n\n"
        result += f"Original image: {image_path}\n"
        if mask_path:
            result += f"Mask image: {mask_path}\n"
        result += f"Edit prompt: {prompt}\n"
        result += f"Parameters: model={model}"
        if size:
            result += f", size={size}"
        if quality:
            result += f", quality={quality}"
        result += f", n={n}\n\n"
        result += "Edited files:\n"
        
        for file_path in saved_files:
            result += f"- {file_path}\n"
        
        return result
        
    except Exception as e:
        return f"Error editing image: {str(e)}"

@mcp.tool()
def create_image_variations(
    working_dir: str,
    image_path: str,
    n: int = 2,
    size: Optional[str] = "1024x1024",
    output_dir: str = "./image_variations",
    filename_prefix: str = "variation"
) -> str:
    """
    Create variations of an existing image using DALL-E 2.
    Only supports dall-e-2 model.
    
    Args:
        working_dir: Absolute path to the working directory for file operations
        image_path: Path to the source image relative to working_dir (must be square PNG, less than 4MB)
        n: Number of variations to generate (1-10, default: 2)
        size: Size of generated variations ("256x256", "512x512", or "1024x1024")
        output_dir: Directory relative to working_dir to save variation images
        filename_prefix: Prefix for variation image filenames
    
    Returns:
        Information about the generated variations and their file paths
    """
    try:
        # Validate parameters
        if n and (n < 1 or n > 10):
            return "Error: Number of variations (n) must be between 1 and 10"
        
        valid_sizes = {"256x256", "512x512", "1024x1024"}
        if size and size not in valid_sizes:
            return f"Error: Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
        
        # Validate working directory
        working_path = Path(working_dir)
        if not working_path.is_absolute():
            return f"Error: working_dir must be an absolute path, got: {working_dir}"
        if not working_path.exists():
            return f"Error: working_dir does not exist: {working_dir}"
        if not working_path.is_dir():
            return f"Error: working_dir is not a directory: {working_dir}"
        
        # Validate image path with clear error messages
        is_valid, error_message, resolved_image_path = validate_image_path(image_path, "read", working_dir)
        if not is_valid:
            return error_message
        
        # Validate image format and requirements for DALL-E 2 variations
        if resolved_image_path.suffix.lower() != '.png':
            return (
                f"Error: Unsupported format for image variations.\n"
                f"• File: '{image_path}'\n"
                f"• Current format: {resolved_image_path.suffix.upper()}\n"
                f"• Required format: PNG\n"
                f"• Suggestion: Convert the image to PNG format using an image editor."
            )
        
        # Check file size (4MB limit for dall-e-2)
        file_size = resolved_image_path.stat().st_size
        if file_size > 4 * 1024 * 1024:
            return (
                f"Error: Image file too large for variations.\n"
                f"• File: '{image_path}'\n"
                f"• Current size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)\n"
                f"• Maximum size: 4,194,304 bytes (4.0 MB)\n"
                f"• Suggestion: Compress or resize the image to reduce file size."
            )
        
        # Check if image is square
        from PIL import Image
        with Image.open(resolved_image_path) as img:
            if img.size[0] != img.size[1]:
                return (
                    f"Error: Image must be square for variations.\n"
                    f"• File: '{image_path}'\n"
                    f"• Current dimensions: {img.size[0]}x{img.size[1]} pixels\n"
                    f"• Required: Square dimensions (width = height)\n"
                    f"• Suggestion: Crop or resize the image to make it square (e.g., 1024x1024)."
                )
        
        # Create output directory relative to working directory
        output_path = working_path / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get OpenAI client
        client = get_openai_client()
        
        # Generate variations
        with open(resolved_image_path, 'rb') as image_file:
            response = client.images.create_variation(
                image=image_file,
                model="dall-e-2",
                n=n or 2,
                size=size or "1024x1024",
                response_format="b64_json"
            )
        
        # Save variation images
        saved_files = []
        timestamp = int(time.time())
        
        for i, image_data in enumerate(response.data):
            # Generate filename
            filename = f"{filename_prefix}_{timestamp}_{i+1}.png"
            file_path = output_path / filename
            
            # Save image
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                if save_base64_image(image_data.b64_json, file_path):
                    saved_files.append(str(file_path))
                else:
                    return f"Error: Failed to save variation {i+1}"
            elif hasattr(image_data, 'url') and image_data.url:
                if download_image_from_url(image_data.url, file_path):
                    saved_files.append(str(file_path))
                else:
                    return f"Error: Failed to download variation {i+1}"
        
        # Format response
        result = f"Successfully created {len(saved_files)} variation(s) of the source image\n\n"
        result += f"Source image: {image_path}\n"
        result += f"Parameters: n={n}, size={size}\n\n"
        result += "Generated variations:\n"
        
        for file_path in saved_files:
            result += f"- {file_path}\n"
        
        return result
        
    except Exception as e:
        return f"Error creating image variations: {str(e)}"

@mcp.tool()
def list_generated_images(working_dir: str, directory: str = "generated_images") -> str:
    """
    List all generated images in a directory with metadata.
    
    Args:
        working_dir: Absolute path to the working directory for file operations
        directory: Directory relative to working_dir to scan for generated images
    
    Returns:
        List of generated images with their metadata
    """
    try:
        # Validate working directory
        working_path = Path(working_dir)
        if not working_path.is_absolute():
            return f"Error: working_dir must be an absolute path, got: {working_dir}"
        if not working_path.exists():
            return f"Error: working_dir does not exist: {working_dir}"
        if not working_path.is_dir():
            return f"Error: working_dir is not a directory: {working_dir}"
        
        # Create directory path relative to working directory
        dir_path = working_path / directory
        if not dir_path.exists():
            return f"Directory '{directory}' does not exist"
        
        if not dir_path.is_dir():
            return f"'{directory}' is not a directory"
        
        # Find image files
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        image_files = []
        
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(file_path)
        
        if not image_files:
            return f"No image files found in '{directory}'"
        
        # Sort by modification time (newest first)
        image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        result = f"Generated Images in '{directory}':\n"
        result += f"Found {len(image_files)} image file(s)\n\n"
        
        from utils.openai_client import get_image_info
        import time
        
        for i, file_path in enumerate(image_files, 1):
            file_stats = file_path.stat()
            image_info = get_image_info(file_path)
            
            result += f"{i}. {file_path.name}\n"
            result += f"   Path: {file_path}\n"
            result += f"   Size: {file_stats.st_size:,} bytes ({file_stats.st_size / 1024 / 1024:.2f} MB)\n"
            result += f"   Modified: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_stats.st_mtime))}\n"
            
            if "error" not in image_info:
                result += f"   Dimensions: {image_info['size'][0]}x{image_info['size'][1]} pixels\n"
                result += f"   Format: {image_info.get('format', 'Unknown')}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error listing generated images: {str(e)}" 