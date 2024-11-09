from billing.models import Wallet
from users.models import Customer
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import redirect
from firebase_admin import auth

from .models import CustomUser
from .tokens import account_activation_token
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt import authentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


class LoginOTPView(APIView):
	permission_classes = [AllowAny]
	authentication_classes = [authentication.JWTAuthentication]
	
	def post(self, request):
		try:
			if request.data.get("token"):
				resp = auth.verify_id_token(request.data.get("token").strip())
				if type(resp)==dict and resp.get("iat") and resp.get("exp") and (resp.get("iat") < resp.get("exp")) and resp.get("phone_number"):
					# login user
					response = {"ok": True, "message": "Login successful."}
					obj_user = CustomUser.objects.get_or_create(phone=resp.get("phone_number"))
					if obj_user[1]:
						customer = Customer.objects.create(user=obj_user[0])
						wallet = Wallet.objects.create(user=customer)
						response.update({"new_user":True})
					else:
						customer = Customer.objects.get(user=obj_user[0])
					obj_user[0].phone_verified = True
					obj_user[0].save()
					refresh = RefreshToken.for_user(obj_user[0])
					refresh['phone'] = obj_user[0].phone
					refresh['cuser_id'] = customer.id
					refresh['user_id'] = obj_user[0].id
					tokens = {
						'refresh': str(refresh),
						'access': str(refresh.access_token)
					}
					response.update({'tokens':tokens})
					return Response(response)
				return Response({"ok": False, "message": f"{resp}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
			else:
				return Response({"ok": False, "message": "Missing request parameteres."}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as err:
			return Response({"ok":False,"message":f"{err}"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
