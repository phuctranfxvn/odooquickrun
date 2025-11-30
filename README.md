# odooquickrun

A simple command-line tool to manage Odoo projects using a **pew-managed virtual environment**.

## 📦 Installation

Install directly from GitHub or your local source:

```bash
pip install odooquickrun
```

## ❌ Uninstallation

To remove the tool:

```bash
pip uninstall odooquickrun
```

## 🚀 Usage

**Prerequisite:** Ensure you have created and activated the `pew` virtual environment for your project before running these commands.

### 🖥️ Odoo Server Operations

**Start Odoo**
```bash
odooquickrun start
```

**Start in Debug Mode**
Running with `debugpy` on port `5678`.
```bash
odooquickrun debug
```

**Upgrade Modules**
Update specific modules in a database.
```bash
odooquickrun upgrade -d <db_name> -m <module1,module2,...>
```
* `-d`: Database name.
* `-m`: Comma-separated list of modules to upgrade.

---

### 🗄️ Database Operations

You can manage your local PostgreSQL databases directly using the `db` command.

> **Note:** The default database port is `5432`. You can specify a custom port for any of the commands below using the `--db-port <port>` option.

#### 1. Database Management

**List all databases** (shows owner and size)
```bash
odooquickrun db info
```

**Drop databases**
Delete one or multiple databases.
```bash
odooquickrun db drop <db1,db2,...> [options]
```
* `<db1,db2,...>`: Comma-separated list of database names (e.g., `test_db,demo_db`).
* `-f` / `--force`: Skip confirmation prompt (useful for automation).

#### 2. User (Role) Management

**List all users** (shows superuser & createdb status)
```bash
odooquickrun db list_users
```

**Create a new user**
Creates a user with `CREATEDB` permission (required for Odoo to create its own databases).
```bash
odooquickrun db create_user <username> <password>
```

**Drop a user**
Permanently delete a postgres user/role.
```bash
odooquickrun db drop_user <username> [-f]
```

---

## 📁 Project Structure

This CLI is designed to be used inside a [pew](https://github.com/berdario/pew)-managed virtualenv containing an Odoo project, structured as follows:

```text
<project_root>/
│
├── odoo/                             # Odoo core (source code)
│
├── addons/
│   ├── custom_3rd_party_addons_1/    # 3rd party modules (OCA, ...)
│   │   ├── module_a/
│   │   ├── module_b/
│   ├── custom_3rd_party_addons_2/
│   │   ├── module_c/
│   │   ├── module_d/
│   ...
│
├── project/                          # Customized modules for project
│   ├── project_module_1/
│   ├── project_module_2/
│   ├── project_module_3/
│
├── config/
    ├── local.conf (or dev.conf)
```

#### Notes:
- You don't need to specify the `addons_path` in the `.conf` file; the script will automatically calculate and prepare it for you based on the folder structure above.

## 🛠 Requirements

- Python 3.7+
- `pew` for managing virtual environments
- `odoo-bin` available in your Odoo project path
- PostgreSQL client tools (`psql`) installed and added to PATH

## 👤 Author

**Phúc Trần Thanh (Felix)**

* 📧 Email: [phuctran.fx.vn@gmail.com](mailto:phuctran.fx.vn@gmail.com)
* 🐙 Github: [@phuctranfxvn](https://github.com/phuctranfxvn)
