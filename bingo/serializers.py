from rest_framework import serializers
from .models import BingoUserInstance, BingoUserTask, BingoTaskTemplate


class BingoTaskTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoTaskTemplate
        fields = "__all__"


class BingoUserTaskSerializer(serializers.ModelSerializer):
    task = BingoTaskTemplateSerializer()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = BingoUserTask
        fields = "__all__"

    def get_photo_url(self, obj):
        if obj.photo_proof:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.photo_proof.url)
        return None


class BingoUserInstanceSerializer(serializers.ModelSerializer):
    tasks = BingoUserTaskSerializer(many=True, read_only=True)

    class Meta:
        model = BingoUserInstance
        fields = "__all__"
