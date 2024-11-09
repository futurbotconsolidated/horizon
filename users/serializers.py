from aouth.models import CustomUser
from billing.models import AstrologyBooking, Coupon, CouponUsage
from astrologer.serializers import AstrologerSerializer
from aouth.serializers import CustomUserSerializer
from users.models import Customer, UserSiteReview, UserBookingReview


from rest_framework.generics import get_object_or_404
from rest_framework import serializers, status
from datetime import datetime, timedelta


# # Customer Model related Serializers
# class CustomerSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Customer
#         fields = ['first_name', 'is_verified', 'last_name', 'full_name', 'date_of_birth',
#                   'place_of_birth', 'gender', 'marital_status', 'occupation', 'phone']





class UserBookingSerializer(serializers.ModelSerializer):
    associate = AstrologerSerializer(read_only=True)
    class Meta:
        model = AstrologyBooking
        fields = '__all__'


class BookingRequestSerializer(serializers.Serializer):
    astrologer = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    user = serializers.IntegerField()
    duration = serializers.IntegerField()
    coupon = serializers.CharField(required=False)

    def validate(self, data):
        user = get_object_or_404(
            Customer, user=self.context.user)
        if self.context.user.id != data['user']:
            raise serializers.ValidationError("Not Authorised.")
        if data.get("coupon"):
            coupon = get_object_or_404(
                Coupon, code=data['coupon'].strip().lower())
            if CouponUsage.objects.filter(coupon=coupon, user=user).count():
                raise serializers.ValidationError(
                    {"coupon": "Invalid Coupon Code."})
            time_difference = (coupon.validity < datetime.now().astimezone())
            if time_difference:
                raise serializers.ValidationError({"coupon":"Invalid Coupon Code."})
            if coupon.plan_specific and data.get("duration") and coupon.plan != int(data.get("duration")):
                raise serializers.ValidationError(
                    {"coupon": "Invalid Coupon Code."})
            if coupon.user_specific and coupon.user != self.context.user:
                raise serializers.ValidationError({"coupon":"Invalid Coupon Code."})
        time_difference = (data['start_time'] < datetime.now().astimezone(
        )+timedelta(minutes=10))
        if time_difference:
            raise serializers.ValidationError("Start time cannot be within next 10 minutes.")
        return data

class CustomerSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = Customer
        fields = ['date_of_birth', 'place_of_birth', 'marital_status', 'occupation', 'user']




class FeedbackCustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source = 'user.full_name')
    avatar = serializers.CharField(source = 'user.avatar')
    class Meta:
        model = Customer
        fields =['name','avatar']

class get_customer(serializers.PrimaryKeyRelatedField):
    def to_representation(self, instance):
        customer_obj = get_object_or_404(Customer, pk = instance.pk)
        serializer = FeedbackCustomerSerializer(customer_obj)
        return serializer.data

    def get_queryset(self):
        return Customer.objects.all()

class UserSiteReviewSerializer(serializers.ModelSerializer):
    customer = get_customer()

    class Meta:
        model = UserSiteReview
        fields = ['customer','rating','review']

    def validate(self, data):
        if not 0 < data['rating'] <= 5:
            raise serializers.ValidationError({"rating":"rating should be between 0 and 5"})
        return data

class UserBookingReviewSerializer(serializers.ModelSerializer):
    customer = get_customer()

    class Meta:
        model = UserBookingReview
        fields = ['customer','booking','rating','review']

    def validate(self, data):
        if not 0 < data['rating'] <= 5:
            raise serializers.ValidationError({"rating":"rating should be between 0 and 5"})
        return data