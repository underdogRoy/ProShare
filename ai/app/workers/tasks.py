from ai.app.services.cache import set_cached
from ai.app.services.summarizer import summarize_article
from ai.app.workers.celery_app import celery_app


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3}, time_limit=60)
def generate_summary_task(self, article_id: int, content: str, method: str) -> dict:
    self.update_state(state="PROGRESS", meta={"step": "summarizing"})
    summary = summarize_article(content, method)
    set_cached(article_id, method, summary)
    self.update_state(state="PROGRESS", meta={"step": "merging"})
    return {"summary": summary}
