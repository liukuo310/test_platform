from django.db import models


class Url(models.Model):
    base_url = models.CharField(max_length=60, verbose_name="域名")
    name = models.CharField(max_length=60, verbose_name="域名服务名称")


class Api(models.Model):
    """接口表"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=60, verbose_name="接口名称", null=True)
    hoster_name = models.CharField(max_length=60, verbose_name="作者名称", null=True)
    base_url = models.CharField(max_length=60, verbose_name="接口域名", null=True)
    api_path = models.CharField(max_length=60, verbose_name="接口地址", null=True)
    headers = models.CharField(max_length=60, verbose_name="请求头", null=True)
    method = models.CharField(max_length=60, verbose_name="请求方式", null=True)
    body = models.CharField(max_length=60, verbose_name="请求体", null=True)
    params = models.CharField(max_length=60, verbose_name="请求参数", null=True)
    desc = models.CharField(max_length=60, verbose_name="接口注释", null=True)
    publish = models.BooleanField(verbose_name="接口是否发布", null=True)
    def to_dict(self):
        return {
            "name": self.name,
            "hoster_name": self.hoster_name,
            "base_url": self.base_url,
            "api_path": self.api_path,
            "headers": self.headers,
            "method": self.method,
            "body": self.body,
            "params": self.params,
            "desc": self.desc,
            "publish": self.publish
        }


class ApiUsing(models.Model):
    case_id = models.ForeignKey("Case", on_delete=models.CASCADE)
    hoster_name = models.CharField(max_length=60, verbose_name="作者名称")
    api_id = models.CharField(max_length=60, verbose_name="接口ID")
    params = models.CharField(max_length=60, verbose_name="请求参数")
    headers = models.CharField(max_length=60, verbose_name="请求头")
    body = models.CharField(max_length=60, verbose_name="请求体")
    method = models.CharField(max_length=60, verbose_name="请求方式")
    assert_result = models.CharField(max_length=60, verbose_name="预期结果")
    globla_values = models.CharField(max_length=60, verbose_name="全局变量")


class Case(models.Model):
    name = models.CharField(max_length=60, verbose_name="用例名称")
    hoster_name = models.CharField(max_length=60, verbose_name="作者名称")
    publish = models.BooleanField(verbose_name="用例是否发布")
    api_ids = models.JSONField(verbose_name="接口ID组合")
    annotation = models.CharField(max_length=60, verbose_name="用例注释")
    def to_dict(self):
        return {
            "name": self.name,
            "hoster_name": self.hoster_name,
            "publish": self.publish,
            "api_ids": self.api_ids,
            "annotation": self.annotation
        }