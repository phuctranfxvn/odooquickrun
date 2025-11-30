import sys
import subprocess


def run_db_info(port):
    """
    List all database with name, owner and size
    """
    print(f"▶️ Fetching database info from localhost:{port}...")
    # Query: Get DB Name, Owner, Size in MB (converted from bytes)
    sql_query = (
        "SELECT datname, pg_catalog.pg_get_userbyid(datdba), "
        "(pg_database_size(datname)/1024.0/1024.0) "
        "FROM pg_database "
        "WHERE datistemplate = false "
        "ORDER BY 1;"
    )

    cmd = [
        "psql",
        "-h", "localhost",
        "-p", str(port),
        "-d", "postgres",  # Connect to the maintenance db
        # Tuples only (ignore the default header/footer of psql)
        "-t",
        "-A",             # Unaligned output mode
        "-F", ",",        # Add comma for later split
        "-c", sql_query
    ]

    try:
        # Run and return the output
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(
                "❌ Error querying database. Make sure PostgreSQL is running and accessible.")
            print(f"Details: {result.stderr.strip()}")
            sys.exit(result.returncode)

        rows = result.stdout.strip().split('\n')

        if not rows or rows == ['']:
            print("ℹ️ No databases found.")
            return

        # Width of the table
        w_name = 40
        w_owner = 20
        w_size = 20

        header = f"{'DB Name':<{w_name}} | {'Owner':<{w_owner}} | {'DB Size (MB)':<{w_size}}"
        separator = "-" * len(header)

        print("\n" + separator)
        print(header)
        print(separator)

        total_size = 0.0

        for row in rows:
            if not row:
                continue
            try:
                parts = row.split(',')
                if len(parts) >= 3:
                    name = parts[0]
                    owner = parts[1]
                    size_mb = float(parts[2])
                    total_size += size_mb

                    print(
                        f"{name:<{w_name}} | {owner:<{w_owner}} | {size_mb:<{w_size}.2f}")
            except ValueError:
                continue

        print(separator)
        print(f"{'Total':<{w_name}} | {'':<{w_owner}} | {total_size:<{w_size}.2f}")
        print("\n")

    except FileNotFoundError:
        print("❌ Command 'psql' not found. Please ensure PostgreSQL client tools are installed and in your PATH.")
        sys.exit(1)


def run_db_create_user(port, username, password):
    """
    Create postgres user
    """
    print(f"▶️ Creating user '{username}' on localhost:{port}...")

    # Create user command, allowing to create db
    sql_query = f"CREATE USER \"{username}\" WITH PASSWORD '{password}' CREATEDB;"

    cmd = [
        "psql",
        "-h", "localhost",
        "-p", str(port),
        "-d", "postgres",
        "-c", sql_query
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ User '{username}' created successfully!")
        else:
            err_msg = result.stderr.strip()
            if "already exists" in err_msg:
                print(f"⚠️ User '{username}' already exists.")
            else:
                print(f"❌ Failed to create user. Error:\n{err_msg}")
            sys.exit(result.returncode)

    except FileNotFoundError:
        print("❌ Command 'psql' not found. Please check PostgreSQL installation.")
        sys.exit(1)


def run_db_list_users(port):
    """
    List all postgres users
    """
    print(f"▶️ Fetching user list from localhost:{port}...")

    sql_query = (
        "SELECT rolname, "
        "CASE WHEN rolsuper THEN 'Yes' ELSE 'No' END, "
        "CASE WHEN rolcreatedb THEN 'Yes' ELSE 'No' END "
        "FROM pg_roles "
        "WHERE rolsuper = True "
        "OR rolcreatedb = True "
        "ORDER BY rolname;"
    )

    cmd = [
        "psql", "-h", "localhost", "-p", str(port), "-d", "postgres",
        "-t", "-A", "-F", ",", "-c", sql_query
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error querying users: {result.stderr.strip()}")
            sys.exit(result.returncode)

        rows = result.stdout.strip().split('\n')
        if not rows or rows == ['']:
            print("ℹ️ No users found.")
            return

        # Table width
        w_user = 30
        w_super = 15
        w_createdb = 15

        header = f"{'User Name':<{w_user}} | {'Superuser':<{w_super}} | {'Create DB':<{w_createdb}}"
        separator = "-" * len(header)

        print("\n" + separator)
        print(header)
        print(separator)

        for row in rows:
            if not row:
                continue
            parts = row.split(',')
            if len(parts) >= 3:
                user = parts[0]
                is_super = parts[1]
                can_create = parts[2]
                print(
                    f"{user:<{w_user}} | {is_super:<{w_super}} | {can_create:<{w_createdb}}")

        print(separator + "\n")

    except FileNotFoundError:
        print("❌ Command 'psql' not found.")
        sys.exit(1)


def run_db_drop_user(port, username, force=False):
    """
    Drop Users
    """
    if not force:
        # Confirmation
        confirm = input(
            f"⚠️  Are you sure you want to PERMANENTLY delete user '{username}'? (y/N): ")
        if confirm.lower() != 'y':
            print("🚫 Operation cancelled.")
            return
    else:
        print(f"⚠️  Force deleting user '{username}'...")

    print(f"▶️ Dropping user '{username}' on localhost:{port}...")

    sql_query = f"DROP USER \"{username}\";"
    cmd = [
        "psql", "-h", "localhost", "-p", str(port), "-d", "postgres",
        "-c", sql_query
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"🗑️  User '{username}' deleted successfully!")
        else:
            err_msg = result.stderr.strip()
            if "cannot be dropped because some objects depend on it" in err_msg:
                print(f"❌ Cannot delete user '{username}'.")
                print(
                    "💡 Hint: This user likely owns databases. Delete or reassign those databases first.")
                print(f"   Check databases owned by this user: odooquickrun db info")
            elif "does not exist" in err_msg:
                print(f"⚠️  User '{username}' does not exist.")
            else:
                print(f"❌ Failed to delete user. Error:\n{err_msg}")
            sys.exit(result.returncode)

    except FileNotFoundError:
        print("❌ Command 'psql' not found.")
        sys.exit(1)


def run_db_drop(port, db_names_str, force=False):
    """
    Drop one or more Databases (comma-separated).
    Automatically kills connections before dropping.
    """
    # 1. Parse database list from input string (e.g., "db1, db2")
    db_list = [name.strip()
               for name in db_names_str.split(',') if name.strip()]

    if not db_list:
        print("❌ No valid database names provided.")
        return

    # 2. Ask for confirmation (if force flag is not set)
    if not force:
        print(f"⚠️  You are about to PERMANENTLY delete the following databases:")
        for db in db_list:
            print(f"   - {db}")

        confirm = input("❓ Are you sure you want to continue? (y/N): ")
        if confirm.lower() != 'y':
            print("🚫 Operation cancelled.")
            return

    # 3. Loop and drop each database
    for dbname in db_list:
        print(f"▶️ Processing '{dbname}' on localhost:{port}...")

        # SQL: Terminate all connections to this specific database
        # (excluding the current connection performing the query)
        kill_query = (
            f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
            f"FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{dbname}' "
            f"AND pid <> pg_backend_pid();"
        )

        # SQL: Drop the database
        drop_query = f"DROP DATABASE \"{dbname}\";"

        # We must connect to 'postgres' system db to perform administrative tasks
        cmd_base = ["psql", "-h", "localhost",
                    "-p", str(port), "-d", "postgres", "-c"]

        try:
            # Step 3a: Kill connections
            # (No need to check output; it's fine if no connections exist)
            subprocess.run(cmd_base + [kill_query], capture_output=True)

            # Step 3b: Drop DB
            result = subprocess.run(
                cmd_base + [drop_query], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"   ✅ Database '{dbname}' deleted successfully!")
            else:
                err_msg = result.stderr.strip()
                if "does not exist" in err_msg:
                    print(
                        f"   ⚠️  Database '{dbname}' does not exist (skipped).")
                else:
                    print(
                        f"   ❌ Failed to delete '{dbname}'. Error: {err_msg}")

        except FileNotFoundError:
            print("❌ Command 'psql' not found.")
            sys.exit(1)
