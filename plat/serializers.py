from rest_framework import serializers
from .models import User


class UserDetailSerialize(serializers.ModelSerializer):
    """用户个人中心详细信息序列化器"""
    # count = serializers.CharField(max_length=60)
    # password = serializers.CharField(max_length=60)

    class Meta:
        model = User  # 明确模型继承
        fields = ("count", "password")
