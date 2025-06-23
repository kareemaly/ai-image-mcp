from pathlib import Path

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