import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///./shared_test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-32-chars-minimum!!")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
