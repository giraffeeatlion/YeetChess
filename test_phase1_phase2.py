#!/usr/bin/env python3
"""
YeetChess Comprehensive Test Suite - Phase 1 & Phase 2
Tests all infrastructure and API implementations.
"""

import os
import sys
import json
from pathlib import Path

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

results = []

def test(name, condition, details=""):
    """Record test result"""
    status = f"{GREEN}✓{RESET}" if condition else f"{RED}✗{RESET}"
    results.append((name, condition))
    print(f"{status} {name}")
    if details and not condition:
        print(f"  {YELLOW}→ {details}{RESET}")

def section(title):
    """Print section header"""
    print(f"\n{BLUE}{BOLD}{title}{RESET}")
    print("=" * 60)

# ============================================================================
# PHASE 1: Infrastructure Tests
# ============================================================================

section("PHASE 1: Monorepo Scaffolding & Infrastructure")

# Git
test("Git repository initialized", Path(".git").exists(), "No .git directory found")
test(".gitignore exists and not empty", 
     Path(".gitignore").exists() and len(Path(".gitignore").read_text()) > 0,
     ".gitignore missing or empty")
test(".gitattributes exists", Path(".gitattributes").exists(), ".gitattributes missing")

# Docker Compose
test("docker-compose.yml exists", Path("docker-compose.yml").exists(), "docker-compose.yml missing")
if Path("docker-compose.yml").exists():
    compose_content = Path("docker-compose.yml").read_text()
    test("Docker Compose has db service", "db:" in compose_content, "db service not found")
    test("Docker Compose has redis service", "redis:" in compose_content, "redis service not found")
    test("PostgreSQL port configured", "5434:5432" in compose_content, "Port mapping not found (should be 5434:5432)")
    test("Redis port configured", "6379:6379" in compose_content, "Redis port not found")

# Root config files
test("README.md exists", Path("README.md").exists(), "README.md missing")
test(".env.example exists and documented", 
     Path(".env.example").exists() and "DATABASE_URL" in Path(".env.example").read_text(),
     ".env.example missing or incomplete")

# Frontend
section("PHASE 1: Frontend (Vite + React + TypeScript)")

test("frontend/ directory exists", Path("frontend").is_dir(), "frontend directory missing")
test("frontend/package.json exists", Path("frontend/package.json").exists(), "package.json missing")
test("frontend/tsconfig.json exists", Path("frontend/tsconfig.json").exists(), "tsconfig.json missing")
test("frontend/vite.config.ts exists", Path("frontend/vite.config.ts").exists(), "vite.config.ts missing")
test("frontend/src/main.tsx exists", Path("frontend/src/main.tsx").exists(), "main.tsx missing")
test("frontend/.nvmrc exists", Path("frontend/.nvmrc").exists(), ".nvmrc missing (Node version pinning)")
test("frontend/.env.example exists", Path("frontend/.env.example").exists(), ".env.example missing")
test("frontend/node_modules exists", Path("frontend/node_modules").exists(), "node_modules not installed")

# Backend
section("PHASE 1: Backend (FastAPI + Poetry + Python 3.12)")

test("backend/ directory exists", Path("backend").is_dir(), "backend directory missing")
test("backend/pyproject.toml exists", Path("backend/pyproject.toml").exists(), "pyproject.toml missing")
test("backend/poetry.lock exists", Path("backend/poetry.lock").exists(), "poetry.lock missing")
test("backend/main.py exists", Path("backend/main.py").exists(), "main.py missing")
test("backend/.env.example exists", Path("backend/.env.example").exists(), ".env.example missing")
test("backend/README.md exists", Path("backend/README.md").exists(), "README.md missing")
test("backend/init.sql exists and not empty", 
     Path("backend/init.sql").exists() and len(Path("backend/init.sql").read_text()) > 50,
     "init.sql missing or too small")

# Verify init.sql has schema
if Path("backend/init.sql").exists():
    init_sql = Path("backend/init.sql").read_text()
    test("init.sql defines users table", "CREATE TABLE users" in init_sql, "users table not defined")
    test("init.sql defines games table", "CREATE TABLE games" in init_sql, "games table not defined")
    test("init.sql has indexes", "CREATE INDEX" in init_sql, "no indexes found")

# Bots
section("PHASE 1: Bot Worker Scaffolding")

test("bots/ directory exists", Path("bots").is_dir(), "bots directory missing")
test("bots/pyproject.toml exists", Path("bots/pyproject.toml").exists(), "bots/pyproject.toml missing")
test("bots/main.py exists", Path("bots/main.py").exists(), "bots/main.py missing")

# ============================================================================
# PHASE 2: Backend Implementation Tests
# ============================================================================

section("PHASE 2: Core Data Models & REST API")

# Config
test("backend/config.py exists", Path("backend/config.py").exists(), "config.py missing")
config_content = Path("backend/config.py").read_text() if Path("backend/config.py").exists() else ""
test("config.py defines Settings class", "class Settings" in config_content, "Settings class not found")
test("config.py has database_url", "database_url" in config_content, "database_url not defined")
test("config.py has jwt_secret_key", "jwt_secret_key" in config_content, "jwt_secret_key not defined")

# Database
test("backend/database.py exists", Path("backend/database.py").exists(), "database.py missing")
db_content = Path("backend/database.py").read_text() if Path("backend/database.py").exists() else ""
test("database.py has AsyncGenerator import", "AsyncGenerator" in db_content, "AsyncGenerator not imported")
test("database.py defines get_db()", "async def get_db()" in db_content, "get_db function not found")
test("database.py has correct get_db return type", "AsyncGenerator[AsyncSession, None]" in db_content, "get_db type annotation wrong")

# Models
section("PHASE 2: ORM Models")

test("backend/models/ directory exists", Path("backend/models").is_dir(), "models directory missing")
test("backend/models/__init__.py exists", Path("backend/models/__init__.py").exists(), "models/__init__.py missing")
test("backend/models/user.py exists", Path("backend/models/user.py").exists(), "user.py missing")
test("backend/models/game.py exists", Path("backend/models/game.py").exists(), "game.py missing")

models_init = Path("backend/models/__init__.py").read_text() if Path("backend/models/__init__.py").exists() else ""
test("models/__init__.py exports User", "User" in models_init, "User not exported")
test("models/__init__.py exports Game", "Game" in models_init, "Game not exported")

user_py = Path("backend/models/user.py").read_text() if Path("backend/models/user.py").exists() else ""
test("User model defines id, username, email, password_hash", 
     all(x in user_py for x in ["id", "username", "email", "password_hash"]),
     "User model missing fields")

game_py = Path("backend/models/game.py").read_text() if Path("backend/models/game.py").exists() else ""
test("Game model defines white_id, black_id, current_fen, pgn, status",
     all(x in game_py for x in ["white_id", "black_id", "current_fen", "pgn", "status"]),
     "Game model missing fields")

# Schemas
section("PHASE 2: Pydantic Schemas")

test("backend/schemas/ directory exists", Path("backend/schemas").is_dir(), "schemas directory missing")
test("backend/schemas/__init__.py exists", Path("backend/schemas/__init__.py").exists(), "schemas/__init__.py missing")
test("backend/schemas/user.py exists", Path("backend/schemas/user.py").exists(), "user.py missing")
test("backend/schemas/game.py exists", Path("backend/schemas/game.py").exists(), "game.py missing")

schemas_init = Path("backend/schemas/__init__.py").read_text() if Path("backend/schemas/__init__.py").exists() else ""
test("schemas exports UserCreate, UserLogin, TokenResponse",
     all(x in schemas_init for x in ["UserCreate", "UserLogin", "TokenResponse"]),
     "User schemas not exported")

# Security
section("PHASE 2: Security Utilities")

test("backend/utils/ directory exists", Path("backend/utils").is_dir(), "utils directory missing")
test("backend/utils/__init__.py exists", Path("backend/utils/__init__.py").exists(), "utils/__init__.py missing")
test("backend/utils/security.py exists", Path("backend/utils/security.py").exists(), "security.py missing")

security_py = Path("backend/utils/security.py").read_text() if Path("backend/utils/security.py").exists() else ""
test("security.py has hash_password function", "def hash_password" in security_py, "hash_password not defined")
test("security.py has verify_password function", "def verify_password" in security_py, "verify_password not defined")
test("security.py has create_access_token function", "def create_access_token" in security_py, "create_access_token not defined")
test("security.py has create_refresh_token function", "def create_refresh_token" in security_py, "create_refresh_token not defined")
test("security.py has verify_token function", "def verify_token" in security_py, "verify_token not defined")

# API Routes
section("PHASE 2: API Endpoints")

test("backend/api/ directory exists", Path("backend/api").is_dir(), "api directory missing")
test("backend/api/__init__.py exists", Path("backend/api/__init__.py").exists(), "api/__init__.py missing")
test("backend/api/auth.py exists", Path("backend/api/auth.py").exists(), "auth.py missing")
test("backend/api/games.py exists", Path("backend/api/games.py").exists(), "games.py missing")

auth_py = Path("backend/api/auth.py").read_text() if Path("backend/api/auth.py").exists() else ""
test("auth.py has /register endpoint", "@router.post(\"/register\"" in auth_py, "/register endpoint not found")
test("auth.py has /login endpoint", "@router.post(\"/login\"" in auth_py, "/login endpoint not found")
test("auth.py has /refresh endpoint", "@router.post(\"/refresh\"" in auth_py, "/refresh endpoint not found")
test("auth.py has /me endpoint", "@router.get(\"/me\"" in auth_py, "/me endpoint not found")

games_py = Path("backend/api/games.py").read_text() if Path("backend/api/games.py").exists() else ""
test("games.py has POST endpoint", "@router.post" in games_py, "POST endpoint not found")
test("games.py has GET endpoints", "@router.get" in games_py, "GET endpoints not found")

# Main app
main_py = Path("backend/main.py").read_text() if Path("backend/main.py").exists() else ""
test("main.py imports auth_router", "from .api.auth import router as auth_router" in main_py, "auth_router not imported")
test("main.py imports games_router", "from .api.games import router as games_router" in main_py, "games_router not imported")
test("main.py includes auth_router", "app.include_router(auth_router)" in main_py, "auth_router not included")
test("main.py includes games_router", "app.include_router(games_router)" in main_py, "games_router not included")
test("main.py has startup event", "@app.on_event(\"startup\")" in main_py, "startup event missing")
test("main.py has shutdown event", "@app.on_event(\"shutdown\")" in main_py, "shutdown event missing")

# ============================================================================
# Import Tests (Critical)
# ============================================================================

section("Import Resolution Tests")

try:
    from backend.config import settings
    test("✓ backend.config imports", True)
except Exception as e:
    test("✓ backend.config imports", False, str(e))

try:
    from backend.database import get_db, AsyncSession
    test("✓ backend.database imports", True)
except Exception as e:
    test("✓ backend.database imports", False, str(e))

try:
    from backend.models import User, Game
    test("✓ backend.models imports", True)
except Exception as e:
    test("✓ backend.models imports", False, str(e))

try:
    from backend.schemas import UserCreate, GameCreate, TokenResponse
    test("✓ backend.schemas imports", True)
except Exception as e:
    test("✓ backend.schemas imports", False, str(e))

try:
    from backend.utils import hash_password, create_access_token
    test("✓ backend.utils imports", True)
except Exception as e:
    test("✓ backend.utils imports", False, str(e))

try:
    from backend.main import app
    num_routes = len(app.routes)
    test(f"✓ backend.main imports (app has {num_routes} routes)", num_routes > 10, f"Only {num_routes} routes")
except Exception as e:
    test("✓ backend.main imports", False, str(e))

# ============================================================================
# Summary
# ============================================================================

section("Test Summary")

passed = sum(1 for _, result in results if result)
total = len(results)
percentage = (passed / total * 100) if total > 0 else 0

print(f"\n{BOLD}Results:{RESET}")
print(f"  Passed: {GREEN}{passed}{RESET}/{total}")
print(f"  Failed: {RED}{total - passed}{RESET}/{total}")
print(f"  Success Rate: {percentage:.1f}%")

if total - passed > 0:
    print(f"\n{YELLOW}Failed Tests:{RESET}")
    for name, result in results:
        if not result:
            print(f"  - {name}")

if percentage == 100:
    print(f"\n{GREEN}{BOLD}✓ All tests passed! Phase 1 & 2 are complete.{RESET}")
    sys.exit(0)
else:
    print(f"\n{RED}{BOLD}✗ Some tests failed. Review above.{RESET}")
    sys.exit(1)
