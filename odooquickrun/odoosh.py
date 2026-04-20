"""
Support for odoo.sh-style projects.

Parses config.sh and builds the Odoo command replicating the logic from odoo.sh,
including addons path construction, virtualenv resolution, and database handling.
"""
import os
import re
import subprocess
import sys
from pathlib import Path
from contextlib import contextmanager


# ---------------------------------------------------------------------------
# Config Parsing
# ---------------------------------------------------------------------------

def parse_config_sh(config_path=None):
    """
    Parse shell variables from config.sh by sourcing it in a subprocess.

    Returns:
        dict: Parsed configuration variables
    """
    if config_path is None:
        config_path = Path.cwd() / "config.sh"

    if not config_path.exists():
        print(f"❌ config.sh not found at {config_path}")
        sys.exit(1)

    # Source config.sh in a bash subprocess and print all env vars
    # We use `env -i` to start clean, then source the file
    cmd = f'source "{config_path}" && env'
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True,
            env={"HOME": str(Path.home()), "PATH": os.environ.get("PATH", "")}
        )
        if result.returncode != 0:
            print(f"❌ Failed to parse config.sh: {result.stderr.strip()}")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ bash not found. Cannot parse config.sh")
        sys.exit(1)

    # Parse the env output
    env_vars = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            env_vars[key] = value

    # Extract only the config variables we care about
    config_keys = [
        "VERBOSE", "VERSION", "PROJECT", "PROJECT_DIRS", "VENV",
        "IP", "EXTRA_PARAMS", "DB", "MODULE", "EXTRA_ADDONS_PATH",
        "ODOO_ROOT_DIR", "HTTP_PORT", "ENTERPRISE", "THEMES",
        "LOAD", "WORKERS", "CRON_WORKERS", "MULTI_DB",
        "ODOO_BIN_PATH", "ODOO_ADDONS_PATH", "PROJECT_DIRS_MODE",
    ]

    config = {}
    for key in config_keys:
        if key in env_vars:
            config[key] = env_vars[key]

    # Also try a simpler regex-based parse as fallback for variables
    # that might not appear in env (commented-out lines are skipped)
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            match = re.match(r'^(\w+)=(.*)$', line)
            if match:
                key = match.group(1)
                value = match.group(2).strip().strip('"').strip("'")
                if key in config_keys and key not in config:
                    config[key] = value

    return config


# ---------------------------------------------------------------------------
# Path Resolution
# ---------------------------------------------------------------------------

def _expand_path(path_str):
    """Expand ~ and resolve path."""
    return str(Path(path_str.replace("~", str(Path.home()))).resolve())


def get_odoosh_odoo_bin(config):
    """
    Resolve the odoo-bin path.

    Priority:
    1. ODOO_BIN_PATH from config.sh
    2. Check if odoo is installed in the virtualenv
    3. ODOO_ROOT_DIR/odoo/VERSION/odoo-bin
    """
    if "ODOO_BIN_PATH" in config:
        path = _expand_path(config["ODOO_BIN_PATH"])
        if Path(path).exists():
            return path
        print(f"⚠️  ODOO_BIN_PATH={path} does not exist, trying alternatives...")

    odoo_root = _expand_path(config.get("ODOO_ROOT_DIR", "~/code/odoo"))
    version = config.get("VERSION", "17.0")

    # Try ODOO_ROOT_DIR/odoo/VERSION/odoo-bin
    odoo_bin = Path(odoo_root) / "odoo" / version / "odoo-bin"
    if odoo_bin.exists():
        return str(odoo_bin)

    print(f"❌ Cannot find odoo-bin. Searched:")
    print(f"   - {odoo_bin}")
    if "ODOO_BIN_PATH" in config:
        print(f"   - {_expand_path(config['ODOO_BIN_PATH'])}")
    sys.exit(1)


def get_odoosh_addons_path(config):
    """
    Build the addons path replicating odoo.sh's _get_addons_path() logic.

    Sources:
    1. ODOO_ROOT_DIR/odoo/VERSION/addons + ODOO_ROOT_DIR/odoo/VERSION/odoo/addons
    2. Enterprise dir (if ENTERPRISE != 0)
    3. Themes dir (if THEMES == 1)
    4. PROJECT_DIRS (scanned for module directories)
    5. EXTRA_ADDONS_PATH
    """
    odoo_root = _expand_path(config.get("ODOO_ROOT_DIR", "~/code/odoo"))
    version = config.get("VERSION", "17.0")

    # 1. Core Odoo addons
    if "ODOO_ADDONS_PATH" in config:
        addons_parts = [_expand_path(p) for p in config["ODOO_ADDONS_PATH"].split(",")]
    else:
        addons_parts = [
            str(Path(odoo_root) / "odoo" / version / "addons"),
            str(Path(odoo_root) / "odoo" / version / "odoo" / "addons"),
        ]

    # 2. Enterprise
    enterprise = config.get("ENTERPRISE", "1")
    if enterprise != "0":
        enterprise_dir = Path(odoo_root) / "enterprise" / version
        if enterprise_dir.exists():
            addons_parts.append(str(enterprise_dir))
        else:
            print(f"⚠️  Enterprise dir not found: {enterprise_dir}")

    # 3. Themes
    if config.get("THEMES") == "1":
        themes_dir = Path(odoo_root) / "design-themes" / version
        if themes_dir.exists():
            addons_parts.append(str(themes_dir))
        else:
            print(f"⚠️  Themes dir not found: {themes_dir}")

    # 4. PROJECT_DIRS
    project_dirs_str = config.get("PROJECT_DIRS", "")
    project_dirs_mode = config.get("PROJECT_DIRS_MODE", "")

    if project_dirs_str:
        for project_dir in project_dirs_str.split(","):
            project_dir = project_dir.strip()
            if not project_dir:
                continue

            # Resolve relative paths from CWD
            pd = Path(project_dir)
            if not pd.is_absolute():
                pd = Path.cwd() / pd
            pd = pd.resolve()

            if not pd.exists():
                print(f"⚠️  PROJECT_DIR not found: {pd}")
                continue

            if project_dirs_mode == "repo_version_module":
                # Find subdirs matching VERSION
                try:
                    dirs = subprocess.run(
                        ["find", str(pd), "-follow", "-mindepth", "2",
                         "-maxdepth", "2", "-type", "d", "-name", version,
                         "-not", "-empty"],
                        capture_output=True, text=True
                    ).stdout.strip().splitlines()
                except Exception:
                    dirs = []
            else:
                # repo_module mode (default)
                try:
                    dirs = [
                        str(d) for d in pd.iterdir()
                        if d.is_dir() and d.name != ".git"
                    ]
                except Exception:
                    dirs = []

            # Filter: only dirs that contain at least one sub-directory (module)
            for d in dirs:
                d_path = Path(d)
                has_module = False
                try:
                    for sub in d_path.iterdir():
                        if sub.is_dir() and sub.name not in (".git", "setup"):
                            has_module = True
                            break
                except Exception:
                    pass

                if has_module:
                    addons_parts.append(str(d_path))
                else:
                    if config.get("VERBOSE") == "1":
                        print(f"ℹ️  Ignoring {d}: doesn't contain any module")

    # 5. EXTRA_ADDONS_PATH
    extra = config.get("EXTRA_ADDONS_PATH", "")
    if extra:
        for p in extra.split(","):
            p = p.strip()
            if p:
                addons_parts.append(_expand_path(p))

    # Filter out non-existent paths
    valid_paths = []
    for p in addons_parts:
        if Path(p).exists():
            valid_paths.append(p)
        else:
            if config.get("VERBOSE") == "1":
                print(f"⚠️  Addons path does not exist: {p}")

    return ",".join(valid_paths)


def get_odoosh_venv_name(config):
    """
    Get the virtualenv name.

    Priority:
    1. VENV from config.sh
    2. venv-odoo{VERSION_MAJOR} (default convention)
    """
    if "VENV" in config:
        return config["VENV"]

    version = config.get("VERSION", "17.0")
    version_major = version.replace(".0", "")
    return f"venv-odoo{version_major}"


def get_odoosh_db_name(config):
    """
    Get the database name.

    Priority:
    1. DB from config.sh
    2. v{VERSION_MAJOR}e_{PROJECT} (default convention)
    """
    if "DB" in config:
        return config["DB"]

    version = config.get("VERSION", "17.0")
    version_major = version.replace(".0", "")
    enterprise = config.get("ENTERPRISE", "1")
    edition = "e" if enterprise == "1" else "c"
    project = config.get("PROJECT", Path.cwd().name)
    return f"v{version_major}{edition}_{project}"


# ---------------------------------------------------------------------------
# Virtualenv Context Manager
# ---------------------------------------------------------------------------

@contextmanager
def in_odoosh_env(venv_name):
    """
    Context manager to activate a pew-managed virtualenv.
    Same logic as runner.py's in_env() but with the odoo.sh venv name.
    """
    workon_home = Path.home() / ".local" / "share" / "virtualenvs"
    envdir = workon_home / venv_name
    env_bin = envdir / "bin"

    if not envdir.exists():
        print(f"❌ Virtualenv '{venv_name}' does not exist at {envdir}")
        sys.exit(1)

    old_env = os.environ.copy()
    os.environ["VIRTUAL_ENV"] = str(envdir)
    os.environ["PATH"] = str(env_bin) + os.pathsep + os.environ["PATH"]
    os.environ.pop("PYTHONHOME", None)
    os.environ.pop("__PYVENV_LAUNCHER__", None)

    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_env)


# ---------------------------------------------------------------------------
# Command Runner
# ---------------------------------------------------------------------------

def run_odoosh_command(args_list, debug=False):
    """
    Build and run the Odoo command for an odoo.sh-style project.

    This replicates the logic of odoo.sh's _init() + _run() functions.
    """
    config = parse_config_sh()

    # Resolve all paths and settings
    venv_name = get_odoosh_venv_name(config)
    odoo_bin = get_odoosh_odoo_bin(config)
    addons_path = get_odoosh_addons_path(config)
    db_name = get_odoosh_db_name(config)

    version = config.get("VERSION", "17.0")
    ip = config.get("IP", "127.0.0.1")
    http_port = config.get("HTTP_PORT", "8069")
    load = config.get("LOAD", "web,base")
    workers = config.get("WORKERS", "0")
    cron_workers = config.get("CRON_WORKERS", "0")
    extra_params_str = config.get("EXTRA_PARAMS", "")

    # Print info
    project = config.get("PROJECT", Path.cwd().name)
    if config.get("VERBOSE") == "1":
        print(f"📋 Project: {project} | Odoo: {version}")
        print(f"🐍 Virtualenv: {venv_name}")
        print(f"🗃️  Database: {db_name}")
        print(f"🌐 Listening: {ip}:{http_port}")

    # Build command
    cmd = ["python"]
    if debug:
        cmd += ["-m", "debugpy", "--listen", f"{ip}:5678"]

    cmd += [odoo_bin]

    # Database
    multi_db = config.get("MULTI_DB", "0")
    if multi_db != "1":
        cmd += ["-d", db_name]

    # Core params
    cmd += [
        f"--db_host=localhost",
        f"--db_user={os.environ.get('PGUSER', 'openerp')}",
        f"--db_password={os.environ.get('PGPASSWORD', 'openerp')}",
        f"--load={load}",
        f"--http-port={http_port}",
        f"--workers={workers}",
        f"--max-cron-threads={cron_workers}",
        "--limit-time-cpu=3600",
        "--limit-time-real=3600",
        f"--http-interface={ip}",
        f"--addons-path={addons_path}",
    ]

    # Extra params from config.sh
    if extra_params_str:
        # Split carefully, preserving quoted values
        import shlex
        try:
            extra_params = shlex.split(extra_params_str)
        except ValueError:
            extra_params = extra_params_str.split()
        cmd += extra_params

    # Additional args from CLI
    cmd += args_list

    print(f"▶️  Running in virtualenv '{venv_name}': {' '.join(cmd)}")

    with in_odoosh_env(venv_name):
        ret = subprocess.run(cmd)
        if ret.returncode != 0:
            print(
                f"❌ Unable to start due to following error code: {ret.returncode}")
            sys.exit(ret.returncode)


def run_odoosh_upgrade(database, modules, debug=False):
    """
    Run upgrade for an odoo.sh project.

    Args:
        database: Database name (overrides config.sh DB if provided)
        modules: Comma-separated module names
        debug: Enable debugpy
    """
    config = parse_config_sh()

    # CLI -d flag overrides config.sh DB
    if database:
        config["DB"] = database

    # Override for upgrade mode
    config["MULTI_DB"] = "0"

    args = ["-u", modules]
    run_odoosh_command(args, debug=debug)
