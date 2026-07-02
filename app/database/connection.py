import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env ஃபைலை லோடு செய்கிறோம்
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Macha! SUPABASE_URL or SUPABASE_KEY is missing in .env file!")

# சுபாபேஸ் கிளையன்ட்டை இனிஷியலைஸ் செய்கிறோம்
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_db():
    """டேட்டாபேஸ் ஆபரேஷன்களுக்கான கிளையன்ட்டை ரிட்டர்ன் செய்யும் சார்பு"""
    return supabase