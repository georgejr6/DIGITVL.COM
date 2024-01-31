from celery import shared_task, Celery
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

from accounts.models import User


app = Celery('marketplace', broker='redis://localhost:6379/0')


@shared_task
def send_email_after_buying_coins(data):
    email_template_html = 'users/emails/send_email_after_buying_coins.html'
    sender = settings.DEFAULT_FROM_EMAIL
    headers = {'Reply-To': 'noreply.digitvlhub@gmail.com'}
    mail_subject = "Successfully bought the coins"
    html_message = get_template(email_template_html)
    body = "Thank you for purchasing DIGITVL Coins! We add new features to the platform periodically." \
           " By purchasing coins you'll be able to utilize and unlock features such as our Tweet function, " \
           "more upload time and feature song function. The more coins the more perks! Cheers!"
    template_context = {
        'username': data['username'],
        'body': body 

    }
    html_content = html_message.render(template_context)
    email = EmailMultiAlternatives(
        subject=mail_subject, body=body, from_email=sender, to=[data['email']], headers=headers
    )
    email.attach_alternative(html_content, 'text/html')
    email.send(fail_silently=True)
