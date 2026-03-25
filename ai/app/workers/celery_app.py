from celery import Celery

from ai.app.core.config import settings

celery_app = Celery("proshare_ai", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
