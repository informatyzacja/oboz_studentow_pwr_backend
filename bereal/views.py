from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets, mixins

from .serializers import UserSerializer
from .models import BeRealPhoto, BeRealPhotoInteraction
from .serializers import BeRealPhotoSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required

# class UserViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows users to be viewed or edited.
#     """
#     queryset = User.objects.all().order_by('-date_joined')
#     serializer_class = UserSerializer
#     permission_classes = [permissions.IsAuthenticated]


class BerealHomePhotoView(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for BeReal photos.
    """

    queryset = BeRealPhoto.objects.all().order_by("-taken_at")
    serializer_class = BeRealPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(["PUT"])
@login_required
def like_photo(request, pk):
    """
    Endpoint to like a BeReal photo.
    """
    try:
        photo = BeRealPhoto.objects.get(pk=pk)
    except BeRealPhoto.DoesNotExist:
        return Response({"error": "Photo not found"}, status=status.HTTP_404_NOT_FOUND)

    like = request.data.get("like", True)
    # ?like=False would be used to unlike the photo
    if not like:
        interaction = BeRealPhotoInteraction.objects.filter(
            photo=photo, user=request.user, interaction_type=1
        ).first()
        if interaction:
            interaction.delete()
            photo.like_count = max(0, photo.like_count - 1)
            photo.save()
            return Response(
                {"message": "Photo unliked successfully"}, status=status.HTTP_200_OK
            )
        return Response(
            {"message": "You have not liked this photo"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    interaction, created = BeRealPhotoInteraction.objects.get_or_create(
        photo=photo, user=request.user, interaction_type=1  # 1 for like
    )

    if not created:
        return Response(
            {"message": "You have already liked this photo"}, status=status.HTTP_200_OK
        )

    photo.like_count += 1
    photo.save()

    return Response({"message": "Photo liked successfully"}, status=status.HTTP_200_OK)
