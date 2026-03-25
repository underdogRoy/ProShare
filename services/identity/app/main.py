import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from services.shared.app.database import build_engine
from services.shared.app.security import create_token, decode_token, hash_password, verify_password

DATABASE_URL = os.getenv("IDENTITY_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/proshare_identity")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

engine = build_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
auth = HTTPBearer()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    bio: Mapped[str] = mapped_column(String(500), default="")
    expertise_tags: Mapped[str] = mapped_column(String(255), default="")
    links: Mapped[str] = mapped_column(String(255), default="")


class RegisterIn(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileIn(BaseModel):
    bio: str = ""
    expertise_tags: str = ""
    links: str = ""


app = FastAPI(title="Identity Service")
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_token(credentials.credentials, JWT_SECRET)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/auth/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(email=payload.email, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id, JWT_SECRET)}


@app.post("/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token(user.id, JWT_SECRET)}


@app.get("/users/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "bio": user.bio,
        "expertise_tags": user.expertise_tags,
        "links": user.links,
        "is_admin": user.is_admin,
    }


@app.put("/users/me")
def update_profile(payload: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.bio = payload.bio
    user.expertise_tags = payload.expertise_tags
    user.links = payload.links
    db.commit()
    return {"ok": True}
