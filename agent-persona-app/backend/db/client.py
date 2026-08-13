import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from supabase import create_client, Client

# Explicit path: backend/.env, regardless of where the script is run from
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


@lru_cache
def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]  # use the service_role key on the backend, never expose it to the frontend
    return create_client(url, key)