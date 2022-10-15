from django.db import models


class Url(models.Model):
    base_url = models.CharField(max_length=60, verbose_name="域名")
    name = models.CharField(max_length=60, verbose_name="域名服务名称")


class Api(models.Model):
    name = models.CharField(max_length=60, verbose_name="接口名称")
    hoster_name = models.CharField(max_length=60, verbose_name="作者名称")
    url = models.ForeignKey("Url", on_delete=models.CASCADE)
    headers = models.CharField(max_length=60, verbose_name="请求头")
    method = models.CharField(max_length=60, verbose_name="请求方式")
    body = models.CharField(max_length=60, verbose_name="请求体")
    annotation = models.CharField(max_length=60, verbose_name="接口注释")
    case = models.ForeignKey("Case", on_delete=models.CASCADE)


class Case(models.Model):
    name = models.CharField(max_length=60, verbose_name="用例名称")
    hoster_name = models.CharField(max_length=60, verbose_name="作者名称")
    publish = models.BooleanField(verbose_name="用例是否发布")
    api_id = models.CharField(max_length=60, verbose_name="用例名称")
    annotation = models.CharField(max_length=60, verbose_name="用例注释")
