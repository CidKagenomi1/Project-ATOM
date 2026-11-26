import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request

from api.schemas import AccountLoginRequest, AccountRegisterRequest
from api.utils import safe_load_json, safe_print, safe_save_json

try:
    from modules.core.database import MONGODB_CONNECTED, db
except Exception:
    db = None
    MONGODB_CONNECTED = False

ACCOUNTS_FILE = "data/atom_accounts.json"
USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]{3,32}$")

router = APIRouter()


def _get_signing_key() -> bytes:
    """Derive deterministic HMAC signing key from environment configuration."""
    raw_secret = (
        os.getenv("ATOM_AUTH_SECRET")
        or os.getenv("MONGODB_URI")
        or os.getenv("GROQ_API_KEY")
        or "atom-cortex-v4-default-secret-key"
    )
    return hashlib.sha256(f"atom_auth:{raw_secret}".encode("utf-8")).digest()


def normalize_username(username: str) -> str:
    """Normalize and validate username format (3-32 chars: a-z, 0-9, _, ., -)."""
    normalized = (username or "").strip().lower()
    if not USERNAME_PATTERN.match(normalized):
        raise ValueError(
            "Username harus 3-32 karakter (hanya huruf kecil, angka, _, ., atau -)."
        )
    return normalized


def hash_password(password: str, salt: str) -> str:
    """Hash password/PIN with PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        (salt or "").encode("utf-8"),
        100_000,
    ).hex()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_auth_token(username: str, display_name: str) -> str:
    """Create HMAC-SHA256 signed authentication token."""
    payload = {
        "u": username,
        "d": display_name or username,
        "iat": int(time.time()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    payload_b64 = _b64url_encode(payload_bytes)
    sig = hmac.new(
        _get_signing_key(), payload_b64.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_auth_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Verify HMAC signature and decode token payload."""
    if not token or not isinstance(token, str) or "." not in token:
        return None
    try:
        payload_b64, provided_sig = token.strip().split(".", 1)
        expected_sig = hmac.new(
            _get_signing_key(), payload_b64.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(provided_sig, expected_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        username = payload.get("u")
        if not username or not USERNAME_PATTERN.match(str(username)):
            return None
        return {
            "username": str(username),
            "display_name": str(payload.get("d") or username),
        }
    except Exception:
        return None


def extract_user_from_request(
    request: Request, body_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Extract authenticated user from Authorization Bearer, X-Atom-Token, or body token."""
    auth_header = request.headers.get("authorization") or request.headers.get(
        "Authorization"
    )
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        user = verify_auth_token(token)
        if user:
            return user

    header_token = request.headers.get("x-atom-token") or request.headers.get(
        "X-Atom-Token"
    )
    if header_token:
        user = verify_auth_token(header_token)
        if user:
            return user

    if body_token:
        return verify_auth_token(body_token)

    return None


def _find_account(username: str) -> Optional[Dict[str, Any]]:
    """Find an account document by username in MongoDB or local JSON fallback."""
    if MONGODB_CONNECTED:
        try:
            doc = db["accounts"].find_one({"username": username}, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            safe_print(f"[DB ERROR] _find_account failed: {e}")

    local_data = safe_load_json(ACCOUNTS_FILE, {"accounts": {}})
    if isinstance(local_data, dict):
        accounts_map = local_data.get("accounts", {})
        if isinstance(accounts_map, dict):
            return accounts_map.get(username)
    return None


def _save_account(account_doc: Dict[str, Any]) -> None:
    """Persist account document to MongoDB (if connected) and local JSON."""
    clean_doc = {k: v for k, v in account_doc.items() if k != "_id"}
    username = clean_doc["username"]

    if MONGODB_CONNECTED:
        try:
            db["accounts"].update_one(
                {"username": username}, {"$set": dict(clean_doc)}, upsert=True
            )
        except Exception as e:
            safe_print(f"[DB ERROR] _save_account failed: {e}")

    local_data = safe_load_json(ACCOUNTS_FILE, {"accounts": {}})
    if not isinstance(local_data, dict):
        local_data = {"accounts": {}}
    if not isinstance(local_data.get("accounts"), dict):
        local_data["accounts"] = {}
    local_data["accounts"][username] = clean_doc
    safe_save_json(ACCOUNTS_FILE, local_data)


@router.post("/accounts/register")
async def register_account(payload: AccountRegisterRequest):
    """Register a new lightweight ATOM account."""
    try:
        username = normalize_username(payload.username)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    password = payload.password or ""
    if len(password) < 4:
        raise HTTPException(
            status_code=400, detail="Password/PIN minimal 4 karakter."
        )

    if _find_account(username):
        raise HTTPException(
            status_code=400,
            detail="Username sudah terdaftar. Silakan masuk atau pilih username lain.",
        )

    display_name = (payload.display_name or "").strip()[:48] or username
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    now_iso = datetime.now().isoformat()

    account_doc = {
        "username": username,
        "display_name": display_name,
        "salt": salt,
        "password_hash": password_hash,
        "created_at": now_iso,
        "last_login": now_iso,
    }
    _save_account(account_doc)

    token = create_auth_token(username, display_name)
    return {
        "status": "success",
        "user": {"username": username, "display_name": display_name},
        "token": token,
    }


@router.post("/accounts/login")
async def login_account(payload: AccountLoginRequest):
    """Authenticate an existing ATOM account."""
    try:
        username = normalize_username(payload.username)
    except ValueError:
        raise HTTPException(
            status_code=401, detail="Username atau Password/PIN tidak sesuai."
        )

    account = _find_account(username)
    if not account:
        raise HTTPException(
            status_code=401, detail="Username atau Password/PIN tidak sesuai."
        )

    expected_hash = hash_password(payload.password or "", account.get("salt", ""))
    stored_hash = account.get("password_hash", "")
    if not stored_hash or not hmac.compare_digest(expected_hash, stored_hash):
        raise HTTPException(
            status_code=401, detail="Username atau Password/PIN tidak sesuai."
        )

    account["last_login"] = datetime.now().isoformat()
    _save_account(account)

    display_name = account.get("display_name") or username
    token = create_auth_token(username, display_name)
    return {
        "status": "success",
        "user": {"username": username, "display_name": display_name},
        "token": token,
    }


@router.get("/accounts/me")
async def get_current_account(request: Request):
    """Verify token and return current authenticated account."""
    user = extract_user_from_request(request)
    if user:
        return {"authenticated": True, "user": user}
    return {"authenticated": False, "user": None}
