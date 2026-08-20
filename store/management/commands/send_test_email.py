from django.core.management.base import BaseCommand
from django.conf import settings
from orders.models import Order
from orders.emails import send_order_confirmation_email


class Command(BaseCommand):
    help = "Diagnose email configuration and send a test order confirmation email"

    def add_arguments(self, parser):
        parser.add_argument(
            '--to', type=str, help='Recipient email address (defaults to order.email or test@example.com)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== ShopSphere Email Diagnostics ==="))
        self.stdout.write(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        self.stdout.write(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        self.stdout.write(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
        self.stdout.write(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', '(empty)') or '(empty)'}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        self.stdout.write("-----------------------------------")

        order = Order.objects.last()
        if not order:
            self.stdout.write(self.style.WARNING("No orders found in database. Create an order first."))
            return

        if options.get('to'):
            order.email = options['to']

        self.stdout.write(f"Sending test email for Order #{order.order_number} to <{order.email}>...")

        success = send_order_confirmation_email(order)

        if success:
            self.stdout.write(self.style.SUCCESS("[SUCCESS] Email dispatch completed successfully."))
            if 'console' in getattr(settings, 'EMAIL_BACKEND', ''):
                self.stdout.write(self.style.WARNING(
                    "\n--- WHY YOU SEE EMAILS IN TERMINAL INSTEAD OF YOUR INBOX ---\n"
                    "By default in development (DEBUG=True), Django uses the 'Console Email Backend'.\n"
                    "Emails are logged above directly in your terminal/server console.\n\n"
                    "HOW TO SEND REAL EMAILS TO YOUR REAL INBOX:\n"
                    "1. Create a '.env' file in your project root: a:\\shopsphere\\.env\n"
                    "2. Add your SMTP credentials:\n"
                    "   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n"
                    "   EMAIL_HOST=smtp.gmail.com\n"
                    "   EMAIL_PORT=587\n"
                    "   EMAIL_USE_TLS=True\n"
                    "   EMAIL_HOST_USER=your_email@gmail.com\n"
                    "   EMAIL_HOST_PASSWORD=your_gmail_app_password\n"
                    "   DEFAULT_FROM_EMAIL='ShopSphere Store <your_email@gmail.com>'\n"
                ))
            else:
                self.stdout.write(self.style.SUCCESS("Real SMTP email sent! Check recipient inbox and spam folder."))
        else:
            self.stdout.write(self.style.ERROR("[FAILED] Email dispatch failed. See logs above for details."))

