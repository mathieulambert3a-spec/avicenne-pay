import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/avicenne_pay")
SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme_secret_key_very_long_at_least_32_chars")
FERNET_KEY: str = os.getenv("FERNET_KEY", "")
