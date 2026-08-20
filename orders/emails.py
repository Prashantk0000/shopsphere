import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """
    Sends an order confirmation & receipt email to customer's mailbox.
    """
    if not order or not order.email:
        logger.warning(f"Cannot send email for order #{getattr(order, 'order_number', 'unknown')}: No email recipient.")
        return False

    subject = f"Order Confirmation — #{order.order_number} | ShopSphere"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'ShopSphere Store <noreply@shopsphere.com>')
    recipient_list = [order.email]

    context = {
        'order': order,
        'items': order.items.all(),
        'payment': getattr(order, 'payment', None),
        'site_name': 'ShopSphere',
    }

    try:
        html_content = render_to_string('emails/order_confirmation.html', context)
        try:
            text_content = render_to_string('emails/order_confirmation.txt', context)
        except Exception:
            text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        email.encoding = 'utf-8'
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        logger.info(f"Order confirmation email sent successfully to {order.email} for order #{order.order_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order #{order.order_number}: {e}")
        return False
