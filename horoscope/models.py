from django.db import models

# Create your models here.
class Horoscope(models.Model):
    sign = models.CharField(max_length=30)
    hosocope = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.sign