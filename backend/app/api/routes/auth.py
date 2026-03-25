"""Auth routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.middleware.auth import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import login, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(payload, db)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": user.id, "email": user.email, "username": user.username}


@router.post("/login")
def login_route(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return login(payload.email, payload.password, db)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/logout")
def logout():
    return {"message": "ok"}


@router.post("/refresh")
def refresh():
    return {"message": "not_implemented_in_mvp_use_login"}
