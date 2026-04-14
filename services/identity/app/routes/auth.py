from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.shared.app.security import create_token, hash_password, verify_password

from ..deps import JWT_SECRET, get_db
from ..models import User
from ..schemas import ForgotPasswordIn, ForgotPasswordOut, LoginIn, RegisterIn, ResetPasswordIn
from ..services.password_reset import create_reset_token, consume_reset_token
from ..services.mailer import MailConfigurationError, MailDeliveryError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(email=payload.email, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id, JWT_SECRET, is_admin=user.is_admin)}


@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token(user.id, JWT_SECRET, is_admin=user.is_admin)}


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    reset_url = None
    if user:
        try:
            _, reset_url = create_reset_token(db, user)
        except MailConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except MailDeliveryError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ForgotPasswordOut(
        message="If an account matches that email, a password reset link has been sent.",
        reset_url=reset_url,
    )


@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = consume_reset_token(db, payload.token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}
