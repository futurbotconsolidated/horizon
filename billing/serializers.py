from rest_framework import serializers
from .models import AstrologyBooking, Coupon, CouponUsage, WalletPlan, WalletTxn
from datetime import datetime
from django.shortcuts import get_object_or_404
from aouth.models import CustomUser
from users.models import Customer

class AstrologyBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstrologyBooking
        fields = '__all__'


class CouponSerializer(serializers.Serializer):
    code = serializers.CharField()
    value = serializers.IntegerField()
    value_type = serializers.CharField()
    validity = serializers.DateTimeField()
    max_discount_value = serializers.IntegerField()

    def validate(self, data):
        time_difference = (data['validity'] < datetime.now().astimezone(
        ))
        if time_difference:
            raise serializers.ValidationError(
                "Coupon code Expired!")
        return data


class WalletAddRequestSerializer(serializers.Serializer):
    plan = serializers.IntegerField()
    coupon = serializers.CharField(required=False)
    amount = serializers.FloatField(required=False)

    def validate(self, data):
        plan = get_object_or_404(
            WalletPlan, id=data['plan'])
        if data.get("coupon"):
            coupon = get_object_or_404(
                Coupon, code=data['coupon'].strip().lower(), coupon_type='W')
            user = get_object_or_404(CustomUser, id=self.context.user.id)
            customer = get_object_or_404(Customer, user=user)

            if CouponUsage.objects.filter(coupon=coupon, user=customer).count():
                raise serializers.ValidationError(
                    {"coupon": "Invalid Coupon Code."})
            time_difference = (coupon.validity < datetime.now().astimezone())
            if time_difference:
                raise serializers.ValidationError(
                    {"coupon": "Invalid Coupon Code."})
            if coupon.user_specific and coupon.user != customer:
                raise serializers.ValidationError(
                    {"coupon": "Invalid Coupon Code."})
        return data


class WalletTxnSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTxn
        fields = '__all__'



class WalletPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletPlan
        fields = '__all__'
