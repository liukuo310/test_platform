from django.db import models

# Create your models here.


class User(models.Model):
    count = models.CharField(max_length=60)  # 账号
    password = models.CharField(max_length=60)  # 密码
