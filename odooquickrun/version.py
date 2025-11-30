import json
import urllib.request
from odooquickrun.__version__ import __version__

# --- AUTHOR INFO ---
__author__ = "Phúc Trần Thanh (Felix)"
__email__ = "phuctran.fx.vn@gmail.com"
__github__ = "https://github.com/phuctranfxvn"
__pypi_url__ = "https://pypi.org/pypi/odooquickrun/json"

def get_remote_version():
    """Get remote version"""
    try:
        with urllib.request.urlopen(__pypi_url__, timeout=3) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return data['info']['version']
    except Exception:
        return None # Return none If no connection or error
    return None

def show_detailed_version():
    """Show versions """
    print(f"\n🚀 Odoo QuickRun CLI")
    print("---------------------------------------------------")
    
    # 1. Current Version
    print(f"📦 Current Version : {__version__}")
    
    # 2. Remote Version (Fetching...)
    print("🌍 Checking for updates...", end="\r")
    remote_ver = get_remote_version()
    print(" " * 30, end="\r") 
    
    if remote_ver:
        print(f"☁️  Remote Version  : {remote_ver}")

        current_parts = [int(x) for x in __version__.split('.')]
        remote_parts = [int(x) for x in remote_ver.split('.')]
        
        if remote_parts > current_parts:
            print(f"\n⚠️  UPDATE AVAILABLE! A newer version ({remote_ver}) is available.")
            print(f"💡 Run: pip install --upgrade odooquickrun")
        else:
            print(f"✅ You are using the latest version.")
    else:
        print(f"☁️  Remote Version  : (Unable to fetch)")

    # 4. Author Info
    print("\n---------------------------------------------------")
    print(f"👤 Author:   {__author__}")
    print(f"📧 Email:    {__email__}")
    print(f"🐙 Github:   {__github__}")
    print("---------------------------------------------------\n")
