from django.db import models

class TestCase(models.Model):
    case_id = models.AutoField(primary_key=True, verbose_name="用例ID")
    name = models.CharField(max_length=60, verbose_name="用例名称")
    hoster_name = models.CharField(max_length=60, verbose_name="作者名称")
    case_models = models.JSONField(verbose_name="用例步骤", null=True, blank=True, default=list)
    case_tag = models.CharField(max_length=60, verbose_name="用例标签", null=True)
    annotation = models.CharField(max_length=60, verbose_name="用例注释")
    case_setup = models.CharField(max_length=60, verbose_name="用例前置条件", null=True)
    case_teardown = models.CharField(max_length=60, verbose_name="用例后置条件", null=True)
    case_steps = models.JSONField(verbose_name="用例步骤", null=True, blank=True, default=list)
    case_asserts = models.CharField(max_length=1000, verbose_name="用例断言", null=True)
    exec_status = models.JSONField(verbose_name="用例执行状态", null=True, blank=True, default=dict)
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    last_update_person = models.CharField(max_length=60, verbose_name="最后更新人")
    def to_dict(self):
        return {
            "case_id": self.case_id,
            "name": self.name,
            "hoster_name": self.hoster_name,
            "case_models": self.case_models,
            "case_tag": self.case_tag,
            "annotation": self.annotation,
            "case_setup": self.case_setup,
            "case_teardown": self.case_teardown,
            "case_steps": self.case_steps,
            "case_asserts": self.case_asserts,
            "exec_status": self.exec_status,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_update_person": self.last_update_person,
        }
