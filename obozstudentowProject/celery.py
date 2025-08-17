import os

import logging
from django.conf import settings
from django.core.mail import mail_admins

from celery import Celery
from celery.signals import task_failure, setup_logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "obozstudentowProject.settings")

app = Celery("obozstudentowProject")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@task_failure.connect()
def celery_task_failure_email(**kwargs):
    import socket
    from django_celery_results.models import TaskResult

    """ celery 4.0 i nowsze nie mają metody do wysyłania emaili o nieudanych zadaniach,
    więc ten handler zdarzeń ma na celu zastąpić tę funkcjonalność
    """
    task_id = kwargs.get("task_id")
    subject = "[{queue_name}@{host}] Błąd: Zadanie {sender.name} ({task_id}): {exception}".format(
        queue_name="celery",  # `sender.queue` nie istnieje w 4.1?
        host=socket.gethostname(),
        **kwargs,
    )
    task_result = TaskResult.objects.get(task_id=task_id)
    django_admin_url = f"{settings.SITE_URL}/admin/django_celery_results/taskresult/{task_result.id}/change/"
    celery_flower_url = f"{settings.CELERY_FLOWER_URL}/task/{task_id}"
    message = """Zadanie {sender.name} o id {task_id} zgłosiło wyjątek:
    
{exception!r}
Zadanie zostało wywołane z argumentami: {args} i parametrami: {kwargs}.
Treść pełnego śladu stosu:
{einfo}

URL do Django Admin: {django_admin_url}
URL do Celery Flower: {celery_flower_url}
    """.format(
        django_admin_url=django_admin_url, celery_flower_url=celery_flower_url, **kwargs
    )
    mail_admins(subject, message)


@setup_logging.connect
def setup_celery_logging(**kwargs):
    return logging.getLogger("celery")
