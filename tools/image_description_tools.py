import os
from pathlib import Path
from server import mcp
from utils.path_utils import resolve_path, validate_image_path
from utils.openai_client import get_openai_client, encode_image_to_base64, is_valid_image_format, get_image_info
from utils.cache_utils import get_cache

def _analyze_image_with_cache(resolved_path: Path, prompt: str, operation: str, params: dict) -> str:
    """
    Internal function to analyze image with caching support.
    
    Args:
        resolved_path: Resolved path to the image file
        prompt: Prompt for the analysis
        operation: Operation type for cache key
        params: Additional parameters for cache key
        
    Returns:
        Analysis result (from cache or OpenAI API)
    """
    cache = get_cache()
    
    # Try to get cached result first
    cached_result = cache.get_cached_result(resolved_path, operation, params)
    if cached_result:
        return cached_result + "\n\n[Result retrieved from cache]"
    
    # Get image info
    image_info = get_image_info(resolved_path)
    if "error" in image_info:
        return f"Error reading image: {image_info['error']}"
    
    # Check file size (OpenAI has limits)
    max_size = 20 * 1024 * 1024  # 20MB
    if image_info.get("file_size", 0) > max_size:
        return f"Error: Image file is too large ({image_info['file_size']:,} bytes). Maximum size is {max_size:,} bytes."
    
    # Get OpenAI client and analyze image
    client = get_openai_client()
    base64_image = encode_image_to_base64(resolved_path)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_info.get('format', 'jpeg').lower()};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    
    description = response.choices[0].message.content
    
    # Format result
    result = f"Image Analysis for '{resolved_path.name}':\n\nImage Info: {image_info['size'][0]}x{image_info['size'][1]} pixels, {image_info.get('format', 'Unknown')} format\n\nDescription:\n{description}"
    
    # Store result in cache
    cache.store_result(resolved_path, operation, params, result)
    
    return result

@mcp.tool()
def describe_image(image_path: str, prompt: str = "Please describe this image in detail.") -> str:
    """
    Analyze an image and provide a detailed description using OpenAI's Vision API.
    Uses caching to avoid repeated API calls for the same image and prompt.
    
    Args:
        image_path: Path to the image file (supports PNG, JPEG, GIF, WebP)
        prompt: Custom prompt for the image analysis (optional)
    
    Returns:
        Detailed description of the image content
    """
    try:
        # Validate image path with clear error messages
        is_valid, error_message, resolved_path = validate_image_path(image_path, "read")
        if not is_valid:
            return error_message
        
        if not is_valid_image_format(resolved_path):
            return (
                f"Error: Unsupported image format for analysis.\n"
                f"• File: '{image_path}'\n"
                f"• Supported formats: PNG, JPEG, JPG, GIF, WebP\n"
                f"• Suggestion: Convert the image to a supported format or use a different image file."
            )
        
        # Use cached analysis
        params = {"prompt": prompt}
        return _analyze_image_with_cache(resolved_path, prompt, "describe", params)
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

@mcp.tool()
def analyze_image_content(image_path: str, analysis_type: str = "general") -> str:
    """
    Analyze specific aspects of an image using OpenAI's Vision API.
    Uses caching to avoid repeated API calls for the same image and analysis type.
    
    Args:
        image_path: Path to the image file
        analysis_type: Type of analysis - "general", "objects", "text", "colors", "composition", "emotions"
    
    Returns:
        Targeted analysis of the image based on the specified type
    """
    prompts = {
        "general": "Provide a comprehensive description of this image, including objects, people, setting, and overall composition.",
        "objects": "Identify and list all objects, items, and things visible in this image. Be specific and detailed.",
        "text": "Extract and transcribe any text, signs, labels, or written content visible in this image.",
        "colors": "Analyze the color palette, dominant colors, and color scheme of this image. Describe the mood created by the colors.",
        "composition": "Analyze the composition, framing, perspective, lighting, and artistic elements of this image.",
        "emotions": "Describe the emotions, mood, and feelings conveyed by this image. What emotional response might it evoke?"
    }
    
    if analysis_type not in prompts:
        return f"Error: Invalid analysis type. Choose from: {', '.join(prompts.keys())}"
    
    try:
        # Validate image path with clear error messages
        is_valid, error_message, resolved_path = validate_image_path(image_path, "read")
        if not is_valid:
            return error_message
        
        if not is_valid_image_format(resolved_path):
            return (
                f"Error: Unsupported image format for analysis.\n"
                f"• File: '{image_path}'\n"
                f"• Supported formats: PNG, JPEG, JPG, GIF, WebP\n"
                f"• Suggestion: Convert the image to a supported format or use a different image file."
            )
        
        # Use cached analysis
        prompt = prompts[analysis_type]
        params = {"analysis_type": analysis_type, "prompt": prompt}
        return _analyze_image_with_cache(resolved_path, prompt, "analyze", params)
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

@mcp.tool()
def compare_images(image1_path: str, image2_path: str, comparison_focus: str = "similarities and differences") -> str:
    """
    Compare two images and highlight their similarities and differences.
    Uses caching for individual image analysis to improve performance.
    
    Args:
        image1_path: Path to the first image file
        image2_path: Path to the second image file
        comparison_focus: What to focus on in the comparison (e.g., "colors", "objects", "composition", "similarities and differences")
    
    Returns:
        Detailed comparison of the two images
    """
    try:
        # Analyze both images first using the cached describe_image function
        desc1 = describe_image(image1_path, f"Describe this image focusing on {comparison_focus}.")
        if desc1.startswith("Error"):
            return f"Error with first image: {desc1}"
        
        desc2 = describe_image(image2_path, f"Describe this image focusing on {comparison_focus}.")
        if desc2.startswith("Error"):
            return f"Error with second image: {desc2}"
        
        # Format comparison
        return f"Image Comparison - Focus: {comparison_focus}\n\n=== First Image ({image1_path}) ===\n{desc1}\n\n=== Second Image ({image2_path}) ===\n{desc2}"
        
    except Exception as e:
        return f"Error comparing images: {str(e)}"

@mcp.tool()
def get_image_metadata(image_path: str) -> str:
    """
    Get detailed metadata and technical information about an image file.
    Note: This function does not use caching as it reads file system info directly.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Technical metadata and information about the image
    """
    try:
        # Validate image path with clear error messages
        is_valid, error_message, resolved_path = validate_image_path(image_path, "read")
        if not is_valid:
            return error_message
        
        # Get comprehensive image info
        image_info = get_image_info(resolved_path)
        if "error" in image_info:
            return f"Error reading image: {image_info['error']}"
        
        # Get file stats
        file_stats = resolved_path.stat()
        
        metadata = f"""Image Metadata for '{image_path}':

File Information:
- File size: {file_stats.st_size:,} bytes ({file_stats.st_size / 1024 / 1024:.2f} MB)
- Format: {image_info.get('format', 'Unknown')}
- Dimensions: {image_info['size'][0]} x {image_info['size'][1]} pixels
- Color mode: {image_info.get('mode', 'Unknown')}
- Aspect ratio: {image_info['size'][0] / image_info['size'][1]:.2f}
- Total pixels: {image_info['size'][0] * image_info['size'][1]:,}

Path Information:
- Absolute path: {resolved_path.absolute()}
- File extension: {resolved_path.suffix}
- Parent directory: {resolved_path.parent}
"""
        
        return metadata
        
    except Exception as e:
        return f"Error getting image metadata: {str(e)}"

@mcp.tool()
def get_cache_info() -> str:
    """
    Get information about the image analysis cache.
    
    Returns:
        Cache statistics and information
    """
    try:
        cache = get_cache()
        cache_info = cache.get_cache_info()
        
        if 'error' in cache_info:
            return f"Error getting cache info: {cache_info['error']}"
        
        return f"""Image Analysis Cache Information:

Cache Directory: {cache_info['cache_dir']}
Number of cached files: {cache_info['cache_files_count']}
Total cache size: {cache_info['total_size_mb']} MB ({cache_info['total_size_bytes']:,} bytes)

Cache Features:
- Automatic file change detection using SHA-256 hashes
- 30-day cache expiration
- Safe cache key generation using MD5 hashes
- Non-blocking cache operations (failures don't affect main functionality)
"""
        
    except Exception as e:
        return f"Error getting cache information: {str(e)}"

@mcp.tool()
def clear_image_cache() -> str:
    """
    Clear all cached image analysis results.
    
    Returns:
        Result of the cache clearing operation
    """
    try:
        cache = get_cache()
        removed_count = cache.clear_cache()
        return f"Successfully cleared image analysis cache. Removed {removed_count} cached files."
        
    except Exception as e:
        return f"Error clearing cache: {str(e)}" 