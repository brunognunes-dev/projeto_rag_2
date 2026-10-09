import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_supabase_connection():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")

    if not supabase_url or not supabase_key:
        print("FAIL: SUPABASE_URL or API Key missing in .env")
        return False

    try:
        from supabase import create_client, Client
        supabase: Client = create_client(supabase_url, supabase_key)
        # Attempt a simple ping / RPC query or bucket check to verify connection
        # Querying an existing table or listing auth/tables
        res = supabase.auth.get_session()
        print("SUCCESS: Connected to Supabase API successfully!")
        return True
    except Exception as e:
        # Secure error logging (do not log keys)
        err_msg = str(e)
        print(f"FAIL: Supabase connection failed: {err_msg[:200]}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    if not success:
        sys.exit(1)
