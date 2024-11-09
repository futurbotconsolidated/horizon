from django.http.response import Http404
import razorpay
import traceback
import json

from rest_framework.permissions import IsAuthenticated
from django.forms.models import model_to_dict
from .models import (
    AstrologyBooking,
    CouponUsage,
    Coupon,
    Wallet,
    WalletInvoice,
    WalletPlan,
    WalletPlanUsage,
    WalletTxn
)
from .utils import create_order
from .serializers import (
    AstrologyBookingSerializer,
    CouponSerializer,
    WalletAddRequestSerializer,
    WalletPlanSerializer,
    WalletTxnSerializer
)
from users.models import Customer

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework_simplejwt import authentication
from rest_framework.response import Response


class BookingViewSet(generics.ListAPIView):
    authentication_classes = [authentication.JWTAuthentication]
    serializer_class = AstrologyBookingSerializer

    def get_queryset(self):
        queryset = AstrologyBooking.objects.all()
        username = self.kwargs.get('astrologer')
        return queryset.filter(associate__id=username)


class UserCouponCheck(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def post(self, request):
        fail = {"ok": False, "message": "Invalid Coupon Code!"}
        try:
            if request.data.get("coupon"):
                couponCode = request.data.get("coupon").strip().lower()
                coupon = get_object_or_404(Coupon, code=couponCode)
                if CouponUsage.objects.filter(coupon=coupon, user=Customer.objects.get(user=request.user)).count():
                    raise Exception("Invalid Coupon Code!")
                if coupon.plan_specific and request.data.get("duration") and coupon.plan != int(request.data.get("duration")):
                    raise Exception("Invalid Coupon Code!")
                if coupon.user_specific and coupon.user != Customer.objects.get(user=request.user):
                    raise Exception("Invalid Coupon Code!")
                serializer = CouponSerializer(data=model_to_dict(coupon))
                if not serializer.is_valid():
                    raise Exception("Invalid Coupon Code!")
                return Response(serializer.data)
            else:
                return Response(fail, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            traceback.print_exc()
            print("err", e)
            return Response(fail, status=status.HTTP_400_BAD_REQUEST)


# Wallet APIs
class WalletBalCheck(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def get(self, request):
        fail = {"ok": False, "message": "Internal Server Error!"}
        try:
            user = Customer.objects.get(user=request.user)
            wallet = Wallet.objects.get(user=user)
            resp = {"ok": True, "balance": wallet.balance}
            return Response(resp)
        except Exception as e:
            print(e)
            return Response(fail, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WalletPlans(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def get(self, request):
        plans = WalletPlan.objects.all()
        plan_usage = WalletPlanUsage.objects.filter(user=Customer.objects.get(
            user=request.user
            ))
        for usage in plan_usage:
            if usage.plan.single_use:
                plans = plans.exclude(id=usage.plan.id)
        print(plans)
        serializer = WalletPlanSerializer(plans, many=True)
        return Response(serializer.data)


class WalletAddBal(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def post(self, request):
        serializer = WalletAddRequestSerializer
        serializer = serializer(data=request.data, context=request)
        if serializer.is_valid():
            order = create_order(request.data, user=request.user, deposit=True)
            if order:
                payload = {
                    "ok": True,
                    "bookingid": order.id,
                    "paygw_orderid": order.invoice.paygw_order,
                    "orderid": f"{order.invoice.order_id}:{order.id}"
                }
                return Response(payload)
            else:
                return Response(
                    {"ok": False, "message": "Internal Server Error."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                serializer.errors, status=status.HTTP_401_UNAUTHORIZED
                )


class WalletRechargeCallback(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def post(self, request, order):
        try:
            if request.data.get(
                "razorpay_payment_id"
                ) and request.data.get(
                    "razorpay_signature"
                    ):
                txn_id = order.strip()
                txn = get_object_or_404(WalletInvoice, order_id=txn_id)
                txns = WalletTxn.objects.filter(invoice=txn)
                if txns.count():
                    item = txns[0]
                else:
                    raise Http404("No valid TXNs found!")
                response = {
                    'razorpay_payment_id': str(request.data.get(
                        'razorpay_payment_id'
                        )),
                    'razorpay_order_id': str(txn.paygw_order),
                    'razorpay_signature': str(request.data.get(
                        'razorpay_signature'
                        ))
                }
                txn.details = json.dumps(
                    {'rzp': response, 'atht': txn.details})
                if not txn.success:
                    cb_txn = None
                    txn.success = True
                    client = razorpay.Client(auth=settings.RZPAY_AUTH)
                    client.utility.verify_payment_signature(response)
                    txn.save()
                    item.wallet.balance = item.wallet.balance+item.txn_amount_sans_tax
                    item.closing_balance = item.wallet.balance
                    if txns.count() == 2:
                        item.wallet.balance = item.wallet.balance + \
                            txns[1].txn_amount_sans_tax
                        cb_txn = txns[1]
                        cb_txn.closing_balance = item.wallet.balance
                        cb_txn.txn_status = 1
                        print(cb_txn.txn_status)
                    item.wallet.save()
                    item.txn_status = 1
                    item.save()
                    if cb_txn:
                        cb_txn.save()
                return Response(
                    {"ok": True, "message": "Transaction verified."}
                    )
            else:
                return Response(
                    {"ok": False, "message": "Payment verification failed."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        except Exception as err:
            print(err)
            return Response(
                {"ok": False, "message": "Internal Server Error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class WalletTXNViewSet(viewsets.ModelViewSet):
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = WalletTxnSerializer

    def list(self, request):
        customer = Customer.objects.get(user=request.user)
        wallet = Wallet.objects.get(user=customer)
        queryset = WalletTxn.objects.filter(wallet=wallet).order_by(
            '-updated_at'
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
