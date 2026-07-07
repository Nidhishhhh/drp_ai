"""
drp.ai — routers/auth.py
Google OAuth 2.0 + JWT authentication.

Flow:
  1. GET  /api/v1/auth/login      — redirects user to Google
  2. GET  /api/v1/auth/callback   — Google redirects here with code
  3. Exchange code for user info  — create/find user in DB
  4. Return JWT access token
  5. GET  /api/v1/auth/me         — returns current user (requires JWT)
"""
from dotenv import load_dotenv
load_dotenv()
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.session import get_db
from database.models import User
from datetime import datetime, timedelta
from jose import JWTError, jwt
import httpx
import os

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "drp-ai-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


# ── JWT helpers ───────────────────────────────────────────────────────────────
def create_access_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Dependency: get current user from JWT ─────────────────────────────────────
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    user_id = int(payload.get("sub"))

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/login")
async def login():
    """Redirect user to Google OAuth consent screen."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/callback")
async def callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Google redirects here after user consents.
    Exchange code for user info, create/find user, return JWT.
    """
    async with httpx.AsyncClient() as client:
        # Step 1 — Exchange code for tokens
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from Google")

        # Step 2 — Get user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo = userinfo_response.json()

    email = userinfo.get("email")
    name = userinfo.get("name", "")
    picture = userinfo.get("picture", "")

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google")

    # Step 3 — Find or create user in DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # New user — create account
        username = email.split("@")[0]  # use email prefix as username
        user = User(
            email=email,
            username=username,
            hashed_password="google_oauth",  # no password for OAuth users
            is_active=True,
            is_verified=True,  # Google already verified the email
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"[drp.ai] New user created: {email}")
    else:
        print(f"[drp.ai] Existing user logged in: {email}")

    # Step 4 — Issue JWT
    jwt_token = create_access_token(user.id, user.email)

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "picture": picture,
        }
    }


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    """Returns the currently logged-in user's profile."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
    }