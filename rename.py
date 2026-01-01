import os

def smart_rename(old_path, new_name):
    ext = os.path.splitext(old_path)[1]
    new_path = os.path.join(
        os.path.dirname(old_path),
        new_name + ext
    )
    os.rename(old_path, new_path)
    return new_path
