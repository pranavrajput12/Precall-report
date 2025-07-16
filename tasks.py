
from celery import Celery

celery_app = Celery("crewai_workflow")
celery_app.config_from_object("celeryconfig")


@celery_app.task
def run_workflow_task(input_data):
    from workflow import run_workflow

    return run_workflow(**input_data)
