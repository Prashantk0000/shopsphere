import logging
import json
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)

# Safely import optional gateway SDKs
try:
    import razorpay
except ImportError:
    razorpay = None

try:
    import stripe
except ImportError:
    stripe = None


class PaymentGatewayService:
    @staticmethod
    def get_razorpay_client():
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        if razorpay and key_id and key_secret:
            return razorpay.Client(auth=(key_id, key_secret)), key_id
        return None, key_id

    @staticmethod
    def initialize_payment(payment):
        """
        Initializes a payment with the selected gateway or generates sandbox metadata.
        Returns a dict of configuration parameters needed by the frontend template.
        """
        amount_paise = int(payment.amount * 100)
        order = payment.order
        method = payment.method

        res = {
            'method': method,
            'amount': payment.amount,
            'amount_paise': amount_paise,
            'currency': 'INR',
            'order_number': order.order_number,
            'is_sandbox': False,
        }

        # 1. Razorpay Integration
        if method == 'razorpay':
            client, key_id = PaymentGatewayService.get_razorpay_client()
            if client:
                try:
                    rzp_order = client.order.create({
                        'amount': amount_paise,
                        'currency': 'INR',
                        'receipt': order.order_number,
                        'payment_capture': 1,
                    })
                    payment.razorpay_order_id = rzp_order['id']
                    payment.save(update_fields=['razorpay_order_id'])
                    res.update({
                        'razorpay_order_id': rzp_order['id'],
                        'razorpay_key_id': key_id,
                    })
                    return res
                except Exception as e:
                    logger.error(f"Razorpay order creation failed: {e}")

            # Fallback to Sandbox if keys missing or SDK error
            res['is_sandbox'] = True
            res['sandbox_gateway'] = 'Razorpay Test Sandbox'
            return res

        # 2. Stripe Integration
        elif method == 'stripe':
            secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            pub_key = getattr(settings, 'STRIPE_PUBLIC_KEY', '')
            if stripe and secret_key and pub_key:
                stripe.api_key = secret_key
                try:
                    intent = stripe.PaymentIntent.create(
                        amount=amount_paise,
                        currency='inr',
                        metadata={'order_number': order.order_number},
                    )
                    payment.stripe_payment_intent_id = intent['id']
                    payment.save(update_fields=['stripe_payment_intent_id'])
                    res.update({
                        'client_secret': intent['client_secret'],
                        'stripe_public_key': pub_key,
                    })
                    return res
                except Exception as e:
                    logger.error(f"Stripe PaymentIntent creation failed: {e}")

            res['is_sandbox'] = True
            res['sandbox_gateway'] = 'Stripe Test Sandbox'
            return res

        # 3. Direct UPI, Card, PayPal or Fallback Sandbox
        else:
            res['is_sandbox'] = True
            res['sandbox_gateway'] = f"{method.upper()} Instant Gateway"
            return res

    @staticmethod
    def verify_payment(payment, post_data):
        """
        Verifies payment response from frontend form or callback POST data.
        Returns tuple: (success: bool, transaction_id: str, raw_data_str: str)
        """
        method = payment.method

        # 1. Razorpay verification
        if method == 'razorpay' and post_data.get('razorpay_payment_id'):
            client, _ = PaymentGatewayService.get_razorpay_client()
            rzp_payment_id = post_data.get('razorpay_payment_id', '')
            rzp_order_id = post_data.get('razorpay_order_id', payment.razorpay_order_id)
            rzp_signature = post_data.get('razorpay_signature', '')

            if client and rzp_signature:
                try:
                    client.utility.verify_payment_signature({
                        'razorpay_order_id': rzp_order_id,
                        'razorpay_payment_id': rzp_payment_id,
                        'razorpay_signature': rzp_signature
                    })
                    payment.razorpay_payment_id = rzp_payment_id
                    payment.razorpay_signature = rzp_signature
                    return True, rzp_payment_id, json.dumps(post_data.dict())
                except Exception as e:
                    logger.error(f"Razorpay signature verification failed: {e}")
                    return False, '', str(e)
            else:
                # Sandbox mode verification for Razorpay
                txn_id = rzp_payment_id or f"RZP_SANDBOX_{payment.order.order_number}"
                return True, txn_id, json.dumps(post_data.dict())

        # 2. Stripe verification
        elif method == 'stripe' and (post_data.get('payment_intent') or post_data.get('stripe_payment_intent_id')):
            intent_id = post_data.get('payment_intent') or post_data.get('stripe_payment_intent_id')
            secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            if stripe and secret_key:
                stripe.api_key = secret_key
                try:
                    intent = stripe.PaymentIntent.retrieve(intent_id)
                    if intent.status == 'succeeded':
                        return True, intent_id, json.dumps(intent)
                    else:
                        return False, intent_id, f"Stripe status: {intent.status}"
                except Exception as e:
                    logger.error(f"Stripe verification failed: {e}")
                    return False, '', str(e)
            else:
                return True, intent_id or f"STRIPE_SANDBOX_{payment.order.order_number}", json.dumps(post_data.dict())

        # 3. Interactive Sandbox / UPI / Card / PayPal payment verification
        else:
            action = post_data.get('action', 'success')
            if action == 'success' or post_data.get('simulate_status') == 'success':
                txn_id = post_data.get('transaction_id') or f"TXN_{method.upper()}_{payment.order.order_number}"
                return True, txn_id, json.dumps(post_data.dict())
            else:
                return False, '', "Payment cancelled or declined in test gateway."
