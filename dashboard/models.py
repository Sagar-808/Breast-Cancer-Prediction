from django.db import models
from django.contrib.auth.models import User

class Patient(models.Model):
    name = models.CharField(max_length=100)
    uId = models.IntegerField(unique=True) 
    email = models.EmailField(blank=True)  
    address = models.TextField()
    picture = models.ImageField(upload_to='user_pictures/') 
    phone = models.CharField(max_length=15)  
    age = models.IntegerField()
    sex = models.CharField(max_length=6, choices=[('Male', 'Male'), ('Female', 'Female')], default='Female') 
    def __str__(self):
        return self.name
