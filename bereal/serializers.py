from django.contrib.auth.models import Group, User
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required

from .models import BeRealPhoto, BeRealPhotoInteraction, BeRealNotification


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class BeRealPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeRealPhoto
        fields = [
            "id",
            "user",
            "photo_url",
            "photo_url_front",
            "taken_at",
            "is_late",
            "like_count",
            "view_count",
            "photo_liked_by_user",
        ]
        depth = 1

    user = UserSerializer(read_only=True)
    photo_liked_by_user = serializers.SerializerMethodField()

    def get_photo_liked_by_user(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.interactions.filter(
                user=request.user, interaction_type=1
            ).exists()
        return False
