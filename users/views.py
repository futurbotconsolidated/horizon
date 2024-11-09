import razorpay
import json
import os
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template

from rest_framework.generics import get_object_or_404

from billing.models import AstrologyBooking, Invoice
from .models import Customer, UserSiteReview, UserBookingReview
from .serializers import (
    UserBookingSerializer,
    BookingRequestSerializer,
    CustomerSerializer,
    UserSiteReviewSerializer,
    UserBookingReviewSerializer
)
from .utils import create_order

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt import authentication
from aouth.models import CustomUser
from django_filters.rest_framework import DjangoFilterBackend


class UserVerifyCheck(APIView):
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        customer = Customer.objects.filter(user=request.user)
        payload = {
            'profileComplete': False,
            'phoneVerified': False
        }
        if customer.count():
            customer = customer[0]
            payload = {
                "profileComplete": customer.is_complete(),
                "phoneVerified": customer.user.phone_verified
            }
        return Response(payload)


# class UserProfile(viewsets.ModelViewSet):
#     queryset = CustomUser.objects.all()
#     authentication_classes = [authentication.JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     serializer_class = CustomerSerializer

#     def list(self, request):
#         raise MethodNotAllowed('GET', detail='Method "GET" not allowed without lookup.')
    
#     def create(self, request):
#         raise MethodNotAllowed(method='POST')

class UserProfile(APIView):
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = Customer.objects.get(user=request.user)
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)

    def put(self, request):
        serializer = CustomerSerializer
        serializer = serializer(data=request.data, context=request)
        customer = Customer.objects.get(user=request.user)
        # serializer = CustomerSerializer(customer, request.data)

        if serializer.is_valid():
            print(type(request.user))
            user_data = serializer.validated_data['user']
            request.user.full_name = user_data['full_name']
            request.user.gender = user_data['gender']
            request.user.email = user_data['email']
            if user_data.get('first_name'):
                request.user.first_name = ("" or user_data.get('first_name'))
            if user_data.get('last_name'):
                request.user.last_name = ("" or user_data.get('last_name'))
            request.user.save()
            serializer.validated_data.pop('user')
            customer_data = serializer.validated_data
            customer.date_of_birth = customer_data['date_of_birth']
            customer.place_of_birth = customer_data['place_of_birth']
            customer.marital_status = customer_data['marital_status']
            customer.occupation = customer_data['occupation']
            customer.save()
            print(type(serializer.validated_data['date_of_birth']))
            # serializer.save()
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBookingRetrieve(generics.RetrieveAPIView):
    queryset = AstrologyBooking.objects.all()
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserBookingSerializer


class UserBookingList(generics.ListAPIView):
    serializer_class = UserBookingSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        customer = get_object_or_404(Customer, user=user)
        return list(reversed(AstrologyBooking.objects.filter(user=customer)))


class UserBooking(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def post(self, request):
        serializer = BookingRequestSerializer
        serializer = serializer(data=request.data, context=request)
        if serializer.is_valid():
            order = create_order(request.data)
            if order == "Wallet has insufficient funds.":
                return Response(
                    {"ok": False, "message": "Wallet has insufficient funds."},
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )
            if order:
                payload = {
                    "ok": True,
                    "bookingid": order.id,
                    "paygw_orderid": order.invoice.paygw_order,
                    "orderid": f"{order.invoice.order_id}:{order.id}"
                }
                booking_plaintext = get_template('booking-plaintext.html')
                booking_html = get_template('booking.html')
                d = {'item': order}
                send_mail('You have a Booking from AstroThought!',
                          booking_plaintext.render(d),
                          'AstroThought <noreply@spirico.life>',
                          [order.associate.user.email, 'anand@astrothought.com', 'ashok@astrothought.com'],
                          fail_silently=False,
                          html_message=booking_html.render(d))
                user_booking_plaintext = get_template(
                    'user-booking-plaintext.html')
                user_booking_html = get_template('user-booking.html')
                d = {'item': order}
                send_mail('You have a Booking from AstroThought!',
                          user_booking_plaintext.render(d),
                          'AstroThought <noreply@spirico.life>',
                          [order.user.user.email],
                          fail_silently=False,
                          html_message=user_booking_html.render(d))
                return Response(payload)
            else:
                return Response(
                    {"ok": False, "message": "Internal Server Error."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            if "Start time cannot be within next 10 minutes" in str(serializer.errors):
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(
                serializer.errors, status=status.HTTP_401_UNAUTHORIZED
                )


class UserBookingCallback(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]
    
    def post(self, request, order):
        try:
            if request.data.get("razorpay_payment_id") and request.data.get("razorpay_signature"):
                txn_id = order.strip()
                txn = get_object_or_404(Invoice, order_id=txn_id)
                item = get_object_or_404(AstrologyBooking, invoice=txn)
                response = {
                    'razorpay_payment_id': str(request.data.get('razorpay_payment_id')),
                    'razorpay_order_id': str(txn.paygw_order),
                    'razorpay_signature': str(request.data.get('razorpay_signature'))
                }
                txn.details = json.dumps({'rzp': response,'atht': txn.details})
                if not txn.success:
                    txn.success = True
                    client = razorpay.Client(auth=settings.RZPAY_AUTH)
                    client.utility.verify_payment_signature(response)
                    txn.save()
                    booking_plaintext = get_template('booking-plaintext.html')
                    booking_html = get_template('booking.html')
                    d = {'item':item}
                    send_mail('You have a Booking from AstroThought!',
                                                 booking_plaintext.render(d),
                                                 'AstroThought <noreply@spirico.life>',
                                                 [item.associate.user.email,'anand@astrothought.com','ashok@astrothought.com'],
                                                 fail_silently=False,
                                                 html_message=booking_html.render(d))
                    user_booking_plaintext = get_template('user-booking-plaintext.html')
                    user_booking_html = get_template('user-booking.html')
                    d = {'item': item}
                    send_mail('You have a Booking from AstroThought!',
                              user_booking_plaintext.render(d),
                              'AstroThought <noreply@spirico.life>',
                              [item.user.user.email],
                              fail_silently=False,
                              html_message=user_booking_html.render(d))
                return Response({"ok": True, "message": "Transaction verified.", "booking": AstrologyBooking.objects.get(invoice=txn).id})
            else:
                return Response({"ok": False, "message": "Payment verification failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as err:
            print(err)
            return Response({"ok":False,"message":"Internal Server Error."},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSiteFeedback(generics.ListCreateAPIView):
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = UserSiteReview.objects.all()
    serializer_class = UserSiteReviewSerializer

    def create(self, request, *args, **kwargs):
        feedback = {
                    'customer': request.user.id,
                    'rating'  : request.data['rating'],
                    'review'  : request.data['review']
                    }
        serializer = UserSiteReviewSerializer(data = feedback)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBookingFeedback(generics.ListCreateAPIView):
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = UserBookingReview.objects.all()
    serializer_class = UserBookingReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking']

    def create(self, request, *args, **kwargs):
        feedback = {
                    'customer': request.user.id,
                    'booking' : request.data['booking'],
                    'rating'  : request.data['rating'],
                    'review'  : request.data['review']
                    }
        if AstrologyBooking.objects.filter(pk = request.data['booking'], completed = False):
            return Response({"message":"booking is not completed yet"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserBookingReviewSerializer(data = feedback)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            print(request.user)
            user = get_object_or_404(CustomUser, username=request.user)
            pic = request.FILES.get('pfp')
            if not pic:
                return Response({
                    "pfp": "upload the picture"
                }, status=status.HTTP_400_BAD_REQUEST)
            if not os.path.exists("static/avatar/"):
                os.mkdir("static/avatar/")
            pic_path = "static/avatar/"+f'{uuid.uuid4()}.jpg'
            with open(pic_path, 'wb+') as f:
                for chunk in pic.chunks():
                    f.write(chunk)
            user.avatar = pic_path
            user.save()
            return Response({
                'ok': True,
                'pfp': user.avatar
            })
        except Exception as err:
            return Response({
                "ok": False, "message": f"{err}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
