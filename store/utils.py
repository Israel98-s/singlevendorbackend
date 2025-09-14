from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def send_order_confirmation_email(order):
    subject = f'Order Confirmation - {str(order.id)[:8]}'
    message = render_to_string('emails/order_confirmation.html', {
        'user': order.user,
        'order': order,
    })
    
    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [order.user.email],
    )
    email.content_subtype = 'html'
    email.send()

def send_payment_confirmation_email(payment):
    subject = f'Payment Confirmation - {payment.reference}'
    message = render_to_string('emails/payment_confirmation.html', {
        'user': payment.order.user,
        'payment': payment,
        'order': payment.order,
    })
    
    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [payment.order.user.email],
    )
    email.content_subtype = 'html'
    email.send()