from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.models import Article, Comment, Report

router = APIRouter(tags=["moderation"])


@router.post("/reports", status_code=201)
def report(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    report_obj = Report(article_id=payload.get("article_id"), comment_id=payload.get("comment_id"), user_id=user.id, reason=payload["reason"])
    db.add(report_obj)
    db.commit()
    return {"id": report_obj.id}


@router.get("/reports")
def reports(_: object = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Report).all()


@router.patch("/reports/{report_id}/status")
def update_report(report_id: int, payload: dict, _: object = Depends(require_admin), db: Session = Depends(get_db)):
    report_obj = db.get(Report, report_id)
    if not report_obj:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    report_obj.status = payload["status"]
    db.add(report_obj)
    db.commit()
    return {"message": "updated"}


@router.delete("/comments/{comment_id}", status_code=204)
def admin_delete_comment(comment_id: int, _: object = Depends(require_admin), db: Session = Depends(get_db)):
    obj = db.get(Comment, comment_id)
    if obj:
        db.delete(obj)
        db.commit()


@router.delete("/articles/{article_id}", status_code=204)
def admin_delete_article(article_id: int, _: object = Depends(require_admin), db: Session = Depends(get_db)):
    obj = db.get(Article, article_id)
    if obj:
        db.delete(obj)
        db.commit()
