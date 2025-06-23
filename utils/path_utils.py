from pathlib import Path
from typing import Tuple, Optional

def resolve_path(file_path: str) -> Path:
    """
    Handle both relative and absolute paths for image files.
    
    Args:
        file_path: Path to the image file, can be:
            - Relative path: "test_data/image.jpg" (resolved relative to current PWD)  
            - Absolute path: "/home/user/images/image.jpg" (used as-is)
    
    Returns:
        Path: Resolved absolute Path object
        
    Examples:
        # Relative path (resolved from current working directory)
        resolve_path("test_data/logo.jpg")
        # Returns: /current/working/directory/test_data/logo.jpg
        
        # Absolute path (used as-is)
        resolve_path("/home/user/images/logo.jpg") 
        # Returns: /home/user/images/logo.jpg
        
        # Works from any directory - relative paths use current PWD
        os.chdir("/some/other/directory")
        resolve_path("../images/logo.jpg")
        # Returns: /some/other/images/logo.jpg
    """
    path = Path(file_path)
    return path if path.is_absolute() else Path.cwd() / path 

def validate_image_path(file_path: str, operation: str = "access") -> Tuple[bool, Optional[str], Optional[Path]]:
    """
    Validate image path with clear error messages for AI agents.
    
    Args:
        file_path: Path to validate (relative or absolute)
        operation: Type of operation ("read", "write", "access")
    
    Returns:
        Tuple of (is_valid, error_message, resolved_path)
        - is_valid: True if path is valid for the operation
        - error_message: None if valid, detailed error message if invalid
        - resolved_path: Resolved Path object if valid, None if invalid
    """
    if not file_path or not file_path.strip():
        return False, "Error: Empty or invalid file path provided. Please provide a valid image file path.", None
    
    # Determine if path is absolute or relative
    is_absolute = file_path.startswith('/')
    path_type = "absolute" if is_absolute else "relative"
    
    try:
        resolved_path = resolve_path(file_path.strip())
        
        # For read operations, check if file exists
        if operation == "read" or operation == "access":
            if not resolved_path.exists():
                return False, (
                    f"Error: Image file not found.\n"
                    f"• Provided path: '{file_path}' ({path_type})\n"
                    f"• Resolved to: '{resolved_path}'\n"
                    f"• Current working directory: '{Path.cwd()}'\n"
                    f"• Suggestion: Verify the file exists and path is correct. "
                    f"Use absolute paths (starting with '/') for files outside current directory."
                ), None
            
            if not resolved_path.is_file():
                return False, (
                    f"Error: Path exists but is not a file.\n"
                    f"• Provided path: '{file_path}' ({path_type})\n"
                    f"• Resolved to: '{resolved_path}'\n"
                    f"• Path type: {'Directory' if resolved_path.is_dir() else 'Other'}\n"
                    f"• Suggestion: Provide a path to an image file, not a directory."
                ), None
        
        # For write operations, check if parent directory exists and is writable
        elif operation == "write":
            parent_dir = resolved_path.parent
            if not parent_dir.exists():
                return False, (
                    f"Error: Output directory does not exist.\n"
                    f"• Provided path: '{file_path}' ({path_type})\n"
                    f"• Output directory: '{parent_dir}'\n"
                    f"• Suggestion: Create the directory first or use an existing directory path."
                ), None
            
            if not parent_dir.is_dir():
                return False, (
                    f"Error: Parent path is not a directory.\n"
                    f"• Provided path: '{file_path}' ({path_type})\n"
                    f"• Parent path: '{parent_dir}'\n"
                    f"• Suggestion: Ensure the parent path is a valid directory."
                ), None
        
        return True, None, resolved_path
        
    except Exception as e:
        return False, (
            f"Error: Invalid file path format.\n"
            f"• Provided path: '{file_path}'\n"
            f"• Error details: {str(e)}\n"
            f"• Suggestion: Use a valid file path. Examples:\n"
            f"  - Relative: 'images/photo.jpg' or './images/photo.jpg'\n"
            f"  - Absolute: '/home/user/images/photo.jpg'"
        ), None 