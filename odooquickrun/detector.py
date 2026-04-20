"""
Auto-detect project type based on files in the working directory.

Detection logic:
- If `config.sh` exists in the project root → "odoosh" project
- Otherwise → "regular" project (standard odooquickrun layout)
"""
from pathlib import Path

PROJECT_TYPE_ODOOSH = "odoosh"
PROJECT_TYPE_REGULAR = "regular"


def detect_project_type():
    """
    Detect the project type based on the current working directory.

    Returns:
        str: PROJECT_TYPE_ODOOSH or PROJECT_TYPE_REGULAR
    """
    base = Path.cwd()
    config_sh = base / "config.sh"

    if config_sh.exists():
        return PROJECT_TYPE_ODOOSH

    return PROJECT_TYPE_REGULAR


def print_detected_type(project_type):
    """Print a user-friendly message about the detected project type."""
    if project_type == PROJECT_TYPE_ODOOSH:
        print("🔍 Detected: odoo.sh project (config.sh found)")
    else:
        print("🔍 Detected: Regular project (standard layout)")
