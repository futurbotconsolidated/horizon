from users.models import Customer
import uuid
import json
import razorpay
import sys
import traceback

from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import APIException
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template

from aouth.models import CustomUser
from astrologer.models import Astrologer
from billing.models import Invoice, AstrologyBooking, GSTPercentage, Coupon, CouponUsage, Wallet, WalletInvoice, WalletTxn


class InsufficientFundException(Exception):
    pass


def get_txn_amount(data):
    
    txn_amount = data["associate"].price * data["duration"]
    gst = 0
    # gst = GSTPercentage.objects.all()
    # if gst.count():
    #     gst=gst[0].percentage/100
    # else:
    #     gst=0.18
    discount = 0
    coupon = None
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
    txn_amount += txn_amount*gst
    txn_amount = round(txn_amount, 2)
    # Get wallet, and check balance
    wallet = Wallet.objects.get(user=data['user'])
    print(txn_amount)
    if wallet.balance >= txn_amount:
        return txn_amount, coupon
    raise InsufficientFundException("Wallet has insufficient funds.")



def create_invoice(data):
    try:
        order_id = str(uuid.uuid4())
        customer_id = data["user"].id
        customer_email = data["user"].user.email
        customer_phone = data["user"].user.phone
        txn_amount, coupon = get_txn_amount(data)
        description = f'Astrologer Booking for User {data["user"].id}'
        details = str(data)
        order = {"id":"booking-"+order_id.split("-")[0]}
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
        return obj_invoice
    except InsufficientFundException as err:
        return "Wallet has insufficient funds."
    except Exception as err:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        return 0


def create_order(data):
    try:
        associate = get_object_or_404(Astrologer, id=data["astrologer"])
        user = get_object_or_404(CustomUser, id=data["user"])
        user = get_object_or_404(Customer, user=user)
        duration = data["duration"]
        start_time = data["start_time"]
        coupon = None
        if data.get("coupon"):
            coupon = data["coupon"].lower().strip()
        data = {
            "associate":associate,
            "user":user,
            "duration":duration,
            "start_time":start_time
        }
        if coupon:
            data.update({"coupon":coupon})
        invoice = create_invoice(data)
        if invoice == "Wallet has insufficient funds.":
            return "Wallet has insufficient funds."
        if invoice:
            obj_wallet = Wallet.objects.get(user=user)
            obj_txn = WalletTxn.objects.create(
                order_type="D",
                wallet=obj_wallet,
                txn_amount=invoice.txn_amount,
                txn_amount_sans_tax=invoice.txn_amount,
                closing_balance=obj_wallet.balance-invoice.txn_amount,
                invoice=invoice,
                description=f"Astrologer Booking with {associate}.",
                txn_status=1
            )
            obj_wallet.balance = obj_wallet.balance-invoice.txn_amount
            obj_wallet.save()
            invoice.success=True
            invoice.save()
            obj_booking = AstrologyBooking.objects.create(
                associate = associate,
                user = user,
                start_time = start_time,
                duration = duration,
                invoice = invoice
            )
            if invoice.coupon:
                CouponUsage.objects.create(
                    coupon=invoice.coupon,
                    invoice=invoice,
                    user=user
                )
            if not obj_booking.invoice.txn_amount:
                item = obj_booking
                booking_plaintext = get_template('booking-plaintext.html')
                booking_html = get_template('booking.html')
                d = {'item': item}
                send_mail('You have a Booking from AstroThought!',
                        booking_plaintext.render(d),
                        'AstroThought <noreply@astrothought.com>',
                        [item.associate.user.email],
                        fail_silently=False,
                        html_message=booking_html.render(d))
                user_booking_plaintext = get_template(
                    'user-booking-plaintext.html')
                user_booking_html = get_template('user-booking.html')
                d = {'item': item}
                send_mail('You have a Booking from AstroThought!',
                        user_booking_plaintext.render(d),
                        'AstroThought <noreply@astrothought.com>',
                        [item.user.user.email],
                        fail_silently=False,
                        html_message=user_booking_html.render(d))
            return obj_booking
        else:
            return 0
    except Exception as err:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        return 0

def number_to_word(number):
    def get_word(n):
        words = { 0:"", 1:"One", 2:"Two", 3:"Three", 4:"Four", 5:"Five", 6:"Six", 7:"Seven", 8:"Eight", 9:"Nine", 10:"Ten", 11:"Eleven", 12:"Twelve", 13:"Thirteen", 14:"Fourteen", 15:"Fifteen", 16:"Sixteen", 17:"Seventeen", 18:"Eighteen", 19:"Nineteen", 20:"Twenty", 30:"Thirty", 40:"Forty", 50:"Fifty", 60:"Sixty", 70:"Seventy", 80:"Eighty", 90:"Ninty" }
        if n <= 20:
            return words[n]
        else:
            ones = n%10
            tens = n-ones
            return words[tens]+" "+words[ones]
            
    def get_all_word(n):
        d = [100,10,100,100]
        v = ["","Hundred And","Thousand","lakh"]
        w = []
        for i,x in zip(d,v):
            t = get_word(n%i)
            if t != "":
                t += " "+x
            w.append(t.rstrip(" "))
            n = n//i
        w.reverse()
        w = ' '.join(w).strip()
        if w.endswith("And"):
            w = w[:-3]
        return w

    arr    = str(number).split(".")
    number = int(arr[0])
    crore  = number//10000000
    number = number%10000000
    word   = ""
    if crore > 0:
        word += get_all_word(crore)
        word += " crore "
    word += get_all_word(number).strip()+" Rupees"
    if len(arr)>1:
        if int(arr[1])==0:
            word += " and "+"zero"+" paisa"
        else:
            word += " and "+get_all_word(int(arr[1]))+" paisa"
    return word
