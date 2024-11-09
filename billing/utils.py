from users.models import Customer
import uuid
import json
import razorpay
import sys
import traceback

from rest_framework.generics import get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template

from billing.models import GSTPercentage, Coupon, CouponUsage, Wallet, WalletInvoice, WalletPlan, WalletPlanUsage, WalletTxn


def create_invoice(data):
    try:
        order_id = str(uuid.uuid4())
        customer_id = data["user"].id
        customer_email = data["user"].user.email
        customer_phone = data["user"].user.phone
        
        txn_amount = data["amount"]
        if not txn_amount:
            txn_amount = data["plan"].inr_amount
        gst = 0
        if data["deposit"]:
            gst = GSTPercentage.objects.all()
            if gst.count():
                gst = gst[0].percentage/100
            else:
                gst = 0.18
        
        discount = 0
        if data.get("coupon"):
            coupon = get_object_or_404(
                Coupon, code=data["coupon"].lower().strip())
            if coupon.value_type == "P":
                discount = coupon.value/100*txn_amount
            if coupon.value_type == "F":
                discount = coupon.value
            if discount > coupon.max_discount_value:
                discount = coupon.max_discount_value
        txn_amount = txn_amount-discount
        txn_amount_sans_tax = txn_amount
        txn_amount += txn_amount*gst
        txn_amount = round(txn_amount, 2)
        description = f'Wallet Invoice for User {data["user"].id}'
        details = str(data)
        # RZP
        client = razorpay.Client(auth=settings.RZPAY_AUTH)
        payload = {
            "amount": txn_amount*100,
            "currency": "INR",
            "receipt": f"{order_id}",
            "notes": {
                "cst_id": customer_id,
                "cst_email": customer_email,
                "cst_phone": customer_phone,
                "plan": data["plan"].id
            }
        }
        print(payload)
        if txn_amount and data["deposit"]:
            order = client.order.create(payload)
        else:
            order = {"id": "booking-"+order_id.split("-")[0]}
        # Raise invoice
        if data.get("coupon"):
            obj_invoice = WalletInvoice.objects.create(
                order_id=order_id,
                customer_id=customer_id,
                customer_email=customer_email,
                customer_phone=customer_phone,
                txn_amount=txn_amount,
                description=description,
                details=json.dumps(details),
                paygw_order=order["id"],
                coupon=coupon
            )
        else:
            obj_invoice = WalletInvoice.objects.create(
                order_id=order_id,
                customer_id=customer_id,
                customer_email=customer_email,
                customer_phone=customer_phone,
                txn_amount=txn_amount,
                description=description,
                details=json.dumps(details),
                paygw_order=order["id"]
            )
        if not txn_amount:
            obj_invoice.success = True
            obj_invoice.save()
        return obj_invoice, txn_amount_sans_tax
    except Exception as err:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        return 0, 0


def create_order(data,user,deposit=False):
    try:
        plan = get_object_or_404(WalletPlan, id=data["plan"])
        amount = (data.get("amount") if data.get("amount") else 0)
        user = get_object_or_404(Customer, user=user)
        wallet = get_object_or_404(Wallet, user=user)
        coupon = None
        if data.get("coupon"):
            coupon = data["coupon"].lower().strip()
        data = {
            "plan": plan,
            "amount": amount,
            "user": user,
            "deposit":deposit
        }
        if coupon:
            data.update({"coupon": coupon})
        invoice, txn_amount_sans_tax = create_invoice(data)
        if invoice:
            txn_amount = invoice.txn_amount
            obj_wal_txn = WalletTxn.objects.create(
                wallet=wallet,
                invoice=invoice,
                order_type=('C' if deposit else 'F'),
                txn_amount=txn_amount,
                txn_amount_sans_tax=txn_amount_sans_tax,
                closing_balance=0,
                description=f"Wallet Recharge for INR {txn_amount_sans_tax}"

            )
            if plan.cashback_percentage:
                obj_cb_txn = WalletTxn.objects.create(
                    wallet=wallet,
                    invoice=invoice,
                    order_type=('C' if deposit else 'F'),
                    txn_amount=(plan.cashback_percentage/100)*txn_amount_sans_tax,
                    txn_amount_sans_tax=(
                        plan.cashback_percentage/100)*txn_amount_sans_tax,
                    closing_balance=0,
                    description=f"Cashback"
                )
            if plan.id != 2:
                WalletPlanUsage.objects.create(
                    plan=plan,
                    user=user,
                    invoice=invoice
                )
            if invoice.coupon:
                CouponUsage.objects.create(
                    coupon=invoice.coupon,
                    invoice=invoice,
                    user=user
                )
            # if not obj_wal_txn.invoice.txn_amount:
            #     item = obj_wal_txn
            #     booking_plaintext = get_template('booking-plaintext.html')
            #     booking_html = get_template('booking.html')
            #     d = {'item': item}
            #     send_mail('You have a Booking from AstroThought!',
            #               booking_plaintext.render(d),
            #               'AstroThought <noreply@astrothought.com>',
            #               [item.associate.email],
            #               fail_silently=False,
            #               html_message=booking_html.render(d))
            #     user_booking_plaintext = get_template(
            #         'user-booking-plaintext.html')
            #     user_booking_html = get_template('user-booking.html')
            #     d = {'item': item}
            #     send_mail('You have a Booking from AstroThought!',
            #               user_booking_plaintext.render(d),
            #               'AstroThought <noreply@astrothought.com>',
            #               [item.user.email],
            #               fail_silently=False,
            #               html_message=user_booking_html.render(d))
            return obj_wal_txn
        else:
            return 0
    except Exception as err:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        return 0
