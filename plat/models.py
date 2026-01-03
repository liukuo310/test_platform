from django.db import models


class User(models.Model):
    uid = models.CharField(max_length=60, verbose_name="主键", primary_key=True)
    count = models.CharField(max_length=60, verbose_name="账号")
    password = models.CharField(max_length=60, verbose_name="密码")
    name = models.CharField(max_length=60, verbose_name="姓名", null=True)
    email = models.CharField(max_length=60, verbose_name="邮箱", null=True)
    objects = models.Manager()
    class Meta:
        db_table = "user"
