from django.db import models

# Create your models here.
class Mappa(models.Model):
    title = models.CharField('title', max_length=15)
    body = models.TextField('comment', max_length=200)

    def __str__(self):
        return self.name