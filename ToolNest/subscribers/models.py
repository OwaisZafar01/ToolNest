
from django.db import models
from django.utils import timezone
import datetime

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    date_subscribed = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        self.date_subscribed = timezone.localtime(timezone.now())
        super(Subscriber, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.email