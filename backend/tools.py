
import os

def list_python_files(folder_path: str) -> list[str]:
    """Find Python files inside a project folder."""
    python_files = []

    for root, _, files in os.walk(folder_path):
        if "venv" in root or "__pycache__" in root:
            continue

        for filename in files:
            if filename.endswith(".py"):
                python_files.append(
                    os.path.join(root, filename)
                )

    return python_files
