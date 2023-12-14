from django.db import models

# Create your models here.
from django.db import models

class XRPLEscrowTransaction(models.Model):
    sender = models.CharField(max_length=100)
    recipient = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=6)
    condition = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    executed = models.BooleanField(default=False)


    def __str__(self):
        return self.sender