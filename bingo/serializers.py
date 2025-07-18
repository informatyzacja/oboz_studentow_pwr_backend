from rest_framework import serializers
from .models import BingoUserInstance, BingoUserTask, BingoTaskTemplate


class BingoTaskTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoTaskTemplate
        fields = "__all__"


class BingoUserTaskSerializer(serializers.ModelSerializer):
    task = BingoTaskTemplateSerializer()

    class Meta:
        model = BingoUserTask
        fields = "__all__"


class BingoUserInstanceSerializer(serializers.ModelSerializer):
    tasks = BingoUserTaskSerializer(many=True, read_only=True)

    class Meta:
        model = BingoUserInstance
        fields = "__all__"
