import os

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "yourusername")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4321").split(",")

API_KEY = os.getenv("API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CV_DATA_DIR = os.getenv("CV_DATA_DIR", "/data/cv")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")          # plain — local dev only
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "") # bcrypt hash — production
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
