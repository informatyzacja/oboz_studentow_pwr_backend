from rest_framework import serializers
from .models import BingoUserInstance, BingoUserTask, BingoTaskTemplate
from .utils import check_bingo_win

class BingoTaskTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoTaskTemplate
        fields = "__all__"


class BingoUserTaskSerializer(serializers.ModelSerializer):
    task = BingoTaskTemplateSerializer()
    photo_proof = serializers.SerializerMethodField()

    class Meta:
        model = BingoUserTask
        fields = "__all__"

    def get_photo_proof(self, obj):
        if obj.photo_proof:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.photo_proof.url)
        return None


class BingoUserInstanceSerializer(serializers.ModelSerializer):
    can_be_submitted = serializers.SerializerMethodField()

    def get_can_be_submitted(self, obj):
        # Bingo można wysłać jeśli jest wygrane i jeszcze nie zostało zatwierdzone (completed_at == None)
        return check_bingo_win(obj) and (obj.completed_at is None)

    class Meta:
        model = BingoUserInstance
        fields = ('id', 'can_be_submitted', ...)
