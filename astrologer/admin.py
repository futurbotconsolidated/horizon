from django.contrib import admin
from .models import Astrologer, Language, Expertise, Favorite

admin.site.register(Astrologer)
admin.site.register(Language)
admin.site.register(Expertise)
admin.site.register(Favorite)