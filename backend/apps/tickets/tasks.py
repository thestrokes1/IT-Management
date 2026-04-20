import time
import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def send_ticket_creation_notification(ticket_id, actor_id):
    logger.info(f'[Celery] Preparing email notification for Ticket #{ticket_id} triggered by User={actor_id}...')
    time.sleep(3)
    logger.info(f'[Celery] Email sent successfully for Ticket #{ticket_id}!')
    return f'Ticket {ticket_id} email processed'
