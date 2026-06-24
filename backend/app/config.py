import os

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "yourusername")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4321").split(",")
