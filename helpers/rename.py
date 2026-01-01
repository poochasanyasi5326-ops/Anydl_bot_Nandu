import os

def smart_rename(original_path: str, new_name: str) -> str:
    ext = os.path.splitext(original_path)[1]
    new_path = os.path.join(os.path.dirname(original_path), new_name + ext)
    os.rename(original_path, new_path)
    return new_path
