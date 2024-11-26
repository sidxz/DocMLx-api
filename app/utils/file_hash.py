import hashlib
import os

def calculate_file_hash(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of the contents of a file.
    
    Args:
        file_path (str): Path to the file.
    
    Returns:
        str: SHA-256 hash of the file contents as a hexadecimal string.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If there are insufficient permissions to read the file.
        ValueError: If the provided file path is not a file.
        IOError: For general I/O errors during file reading.
    """
    # Validate input
    if not isinstance(file_path, str):
        raise TypeError("The file path must be a string.")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
    
    sha256 = hashlib.sha256()

    # Attempt to open and read the file securely
    try:
        with open(file_path, 'rb') as file:
            for chunk in iter(lambda: file.read(8192), b''):
                sha256.update(chunk)
    except PermissionError:
        raise PermissionError(f"Permission denied: {file_path}")
    except IOError as e:
        raise IOError(f"An I/O error occurred while reading the file: {e}")

    return sha256.hexdigest()
