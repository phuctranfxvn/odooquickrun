import argparse
import subprocess
import sys
import os
from pathlib import Path
from contextlib import contextmanager
from .db import run_db_info, run_db_create_user, run_db_list_users, run_db_drop_user, run_db_drop
from .version import show_detailed_version

def get_project_name():
    return Path.cwd().name


def get_addons_path():
    base = Path.cwd()
    addons_root = base / 'addons'
    odoo_addons = [
        base / 'odoo' / 'addons',
        base / 'odoo' / 'odoo' / 'addons',
        base / 'project'
    ]

    custom_addons = []
    ignore_folder_names = [".git"]
    if addons_root.exists():
        for sub in addons_root.iterdir():
            if sub.is_dir() and sub.name not in ignore_folder_names:
                custom_addons.append(str(sub.resolve()))

    paths = custom_addons + [str(p.resolve())
                             for p in odoo_addons if p.exists()]
    return ",".join(paths)


def get_config_path():
    config_folder = Path.cwd() / 'config'
    local_conf = config_folder / 'local.conf'
    dev_conf = config_folder / 'dev.conf'
    server_conf = config_folder / 'server.conf'

    if local_conf.exists():
        return str(local_conf.resolve())
    elif dev_conf.exists():
        return str(dev_conf.resolve())
    elif server_conf.exist():
        return str(server_conf.resolve())
    else:
        print(
            "❌ Unable to find local.conf / dev.conf / server.conf in the folder ./config/")
        sys.exit(1)


@contextmanager
def in_env(name):
    workon_home = Path.home() / '.local' / 'share' / 'virtualenvs'
    envdir = workon_home / name
    env_bin = envdir / 'bin'

    if not envdir.exists():
        print(f"❌ Virtualenv pew '{name}' does not exist {envdir}")
        sys.exit(1)

    old_env = os.environ.copy()
    os.environ['VIRTUAL_ENV'] = str(envdir)
    os.environ['PATH'] = str(env_bin) + os.pathsep + os.environ['PATH']
    os.environ.pop('PYTHONHOME', None)
    os.environ.pop('__PYVENV_LAUNCHER__', None)

    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def run_odoo_command(args_list, debug=False):
    project_name = get_project_name()
    addons_path = get_addons_path()
    config_file = get_config_path()
    odoo_bin = Path.cwd() / 'odoo' / 'odoo-bin'

    if not odoo_bin.exists():
        print("❌ Unable to find odoo-bin in the folder ./odoo/")
        sys.exit(1)

    cmd = ["python"]
    if debug:
        cmd += ["-m", "debugpy", "--listen", "5678"]

    cmd += [
        str(odoo_bin),
        f"--addons-path={addons_path}",
        f"--config={config_file}"
    ] + args_list

    print(f"▶️ Running in virtualenv '{project_name}': {' '.join(cmd)}")
    with in_env(project_name):
        ret = subprocess.run(cmd)
        if ret.returncode != 0:
            print(
                f"❌ Unable to start due to following error code: {ret.returncode}")
            sys.exit(ret.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Odoo project runner with pew env context")
    parser.add_argument(
            "-v", "--version",
            action="store_true",
            help="Show detailed version and author information"
        )

    subparsers = parser.add_subparsers(dest="command")

    # --- START / START WITH DEBUG ---
    subparsers.add_parser("start", help="Start Odoo server")
    subparsers.add_parser(
        "debug", help="Start Odoo server in debug mode (Debug port: 5678)")

    # --- UPGRADE ODOO ---
    parser_upgrade = subparsers.add_parser(
        "upgrade", help="Upgrade Odoo modules")
    parser_upgrade.add_argument(
        "-d", "--database", required=True, help="Database name")
    parser_upgrade.add_argument(
        "-m", "--modules", required=True, help="Comma-separated module names")

    # --- DB ---
    parser_db = subparsers.add_parser("db", help="Database operations")
    parser_db.add_argument("--db-port", default="5432",
                           help="PostgreSQL Port (default: 5432)")
    db_subparsers = parser_db.add_subparsers(dest="db_command")

    # --- DB INFO ---
    db_subparsers.add_parser("info", help="List all databases with size info")

    # --- DB DROP ---
    parser_drop = db_subparsers.add_parser(
        "drop", help="Delete one or more databases")
    parser_drop.add_argument(
        "databases", help="Database names (comma-separated, e.g., db1,db2)")
    parser_drop.add_argument(
        "-f", "--force", action="store_true", help="Force delete without confirmation")

    # --- DB CREATE USER ---
    parser_create_user = db_subparsers.add_parser(
        "create_user", help="Create a new database user")
    parser_create_user.add_argument(
        "username", help="Username for the new DB user")
    parser_create_user.add_argument(
        "password", help="Password for the new DB user")

    # --- DB LISTING USERS ---
    db_subparsers.add_parser("users", help="List all database users/roles")

    # --- DB DROP USER ---
    parser_drop_user = db_subparsers.add_parser(
        "drop_user", help="Delete a database user")
    parser_drop_user.add_argument("username", help="Username to delete")
    parser_drop_user.add_argument(
        "-f", "--force", action="store_true", help="Force delete without confirmation")

    args = parser.parse_args()

    if args.version:
        show_detailed_version()
        sys.exit(0)
    if args.command == "start":
        run_odoo_command([])
    elif args.command == "debug":
        run_odoo_command([], debug=True)
    elif args.command == "upgrade":
        run_odoo_command(["-d", args.database, "-u", args.modules])
    elif args.command == "db":
        if args.db_command == "info":
            run_db_info(args.db_port)
        elif args.db_command == "drop":
            run_db_drop(args.db_port, args.databases, args.force)
        elif args.db_command == "create_user":
            run_db_create_user(args.db_port, args.username, args.password)
        elif args.db_command == "users":
            run_db_list_users(args.db_port)
        elif args.db_command == "drop_user":
            run_db_drop_user(args.db_port, args.username, args.force)
        else:
            parser_db.print_help()
    else:
        parser.print_help()


def runner():
    main()
