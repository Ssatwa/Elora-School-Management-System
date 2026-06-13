from celery import shared_task

from apps.reports.services import generate_report_pdf


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_report_pdf_task(self, report_id, school_id):
    return generate_report_pdf(report_id=report_id, school_id=school_id)
