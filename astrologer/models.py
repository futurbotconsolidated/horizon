from django.db import models
from django.utils.text import slugify 

from aouth.models import CustomUser
from users.models import Customer


# Create your models here.
class Astrologer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    slug = models.CharField(max_length=200, null=True, blank=True)
    price = models.FloatField()
    experience = models.IntegerField()
    rating = models.FloatField()
    penalized = models.BooleanField()
    about = models.CharField(max_length=1000, null=True, blank=True)
    about_seo = models.CharField(max_length=1000, null=True, blank=True)
    title_seo = models.CharField(max_length=1000, null=True, blank=True)
    language = models.ManyToManyField('Language', blank=True)
    expertise = models.ManyToManyField('Expertise', blank=True)
    availibility_start = models.TimeField()
    availibility_end = models.TimeField()
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    online = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = f"astro-{slugify(self.first_name)}-{self.id}"
        super(Astrologer, self).save(*args, **kwargs)

    def __str__(self):
        return self.user.full_name

class Language(models.Model):
    name = models.CharField(max_length=254)

    def __str__(self):
        return self.name


class Expertise(models.Model):
    name= models.CharField(max_length=254)

    def __str__(self):
        return self.name

class Favorite(models.Model):
    astrologer = models.ForeignKey(Astrologer,on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE)

# class AstroReviews(models.Model):
#     customer = 
