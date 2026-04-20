"""
Project scaffolding for odooquickrun.

Creates a new Odoo project with the standard layout:
  <project_name>/
  ├── addons/requirements.txt
  ├── config/dev.conf
  ├── project/requirements.txt
  └── odoo/  (cloned from GitHub)
"""
import os
import sys
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

DEV_CONF_TEMPLATE = """[options]
admin_passwd = admin
without_demo = False
verbose = True
db_user = openerp
db_password = openerp
db_port = 5432
db_host = localhost
db_maxconn = 64
db_template = template1
http_enable = True
http_interface = 0.0.0.0
http_port = 8069
server_wide_modules = base,web
log_level = debug_rpc
data_dir = ./var/storage
list_db = True
translate_modules = ['all']
limit_time_cpu = 3600
limit_time_real = 3600
"""

REQUIREMENTS_TXT_TEMPLATE = """# Add your Python dependencies here
# Example:
# phonenumbers
# python-stdnum
"""

GITIGNORE_TEMPLATE = """# Odoo
*.pyc
__pycache__/
*.pyo
*.egg-info/
dist/
build/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Storage
var/

# OS
.DS_Store
Thumbs.db
"""


# ---------------------------------------------------------------------------
# Init Logic
# ---------------------------------------------------------------------------

def run_init_project(project_name, version="19.0", no_squash=False):
    """
    Scaffold a new Odoo project with the standard odooquickrun layout.

    Args:
        project_name: Name of the project directory to create
        version: Odoo version branch to clone (e.g., "19.0", "17.0")
        no_squash: If True, do a full git clone instead of shallow (depth=1)
    """
    base = Path.cwd()
    project_dir = base / project_name

    # 1. Check if project already exists
    if project_dir.exists():
        print(f"❌ Directory '{project_name}' already exists at {project_dir}")
        sys.exit(1)

    print(f"🚀 Initializing new Odoo project: {project_name}")
    print(f"   📦 Odoo version: {version}")
    print(f"   📂 Location: {project_dir}")
    print()

    # 2. Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # 3. Create addons/ with requirements.txt
    addons_dir = project_dir / "addons"
    addons_dir.mkdir()
    (addons_dir / "requirements.txt").write_text(REQUIREMENTS_TXT_TEMPLATE.lstrip())
    print("   ✅ Created addons/requirements.txt")

    # 4. Create config/ with dev.conf
    config_dir = project_dir / "config"
    config_dir.mkdir()
    (config_dir / "dev.conf").write_text(DEV_CONF_TEMPLATE.lstrip())
    print("   ✅ Created config/dev.conf")

    # 5. Create project/ with requirements.txt
    proj_modules_dir = project_dir / "project"
    proj_modules_dir.mkdir()
    (proj_modules_dir / "requirements.txt").write_text(
        REQUIREMENTS_TXT_TEMPLATE.lstrip())
    print("   ✅ Created project/requirements.txt")

    # 6. Create .gitignore
    (project_dir / ".gitignore").write_text(GITIGNORE_TEMPLATE.lstrip())
    print("   ✅ Created .gitignore")

    # 7. Clone Odoo
    print()
    clone_url = "https://github.com/odoo/odoo.git"
    odoo_dir = project_dir / "odoo"

    if no_squash:
        print(f"   📥 Cloning Odoo {version} (full history)...")
        clone_cmd = [
            "git", "clone",
            "--branch", version,
            "--single-branch",
            clone_url,
            str(odoo_dir)
        ]
    else:
        print(f"   📥 Cloning Odoo {version} (shallow, depth=1)...")
        clone_cmd = [
            "git", "clone",
            "--branch", version,
            "--single-branch",
            "--depth", "1",
            clone_url,
            str(odoo_dir)
        ]

    try:
        result = subprocess.run(clone_cmd)
        if result.returncode != 0:
            print(f"\n   ❌ Failed to clone Odoo. Exit code: {result.returncode}")
            print("   💡 Check your internet connection and that the branch exists.")
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("   ❌ 'git' command not found. Please install Git.")
        sys.exit(1)

    print(f"\n   ✅ Odoo {version} cloned successfully!")

    # 8. Summary
    print()
    print("=" * 50)
    print(f"🎉 Project '{project_name}' created successfully!")
    print("=" * 50)
    print()
    print("📁 Structure:")
    print(f"   {project_name}/")
    print(f"   ├── addons/requirements.txt")
    print(f"   ├── config/dev.conf")
    print(f"   ├── project/requirements.txt")
    print(f"   ├── odoo/  (Odoo {version})")
    print(f"   └── .gitignore")
    print()
    print("📋 Next steps:")
    print(f"   1. cd {project_name}")
    print(f"   2. Create virtualenv: pew new {project_name}")
    print(f"   3. Install Odoo: pip install -e ./odoo")
    print(f"   4. Run: odooquickrun start")
