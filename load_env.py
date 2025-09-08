import os
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).resolve().parent / '.env'
    
    if not env_path.exists():
        print(f"Environment file not found: {env_path}")
        return
    
    with open(env_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

if __name__ == "__main__":
    load_env_file()
    print("Environment variables loaded from .env file")
    print(f"DEBUG: {os.environ.get('DEBUG')}")
    print(f"SECRET_KEY: {'*' * 20 if os.environ.get('SECRET_KEY') else 'NOT SET'}")