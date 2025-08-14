from django.db import models
from django.contrib.auth.models import User  # zakładam, że używasz wbudowanego Usera


class BeRealPhoto(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bereal_photos",
        help_text="Użytkownik, który dodał zdjęcie",
    )
    photo_url = models.ImageField(
        help_text="URL do przechowywanego zdjęcia (tylna kamera)"
    )
    photo_url_front = models.ImageField(
        help_text="URL do przechowywanego zdjęcia (przednia kamera)"
    )
    taken_at = models.DateTimeField(help_text="Data i godzina wykonania zdjęcia")
    is_late = models.BooleanField(
        default=False, help_text="Czy zdjęcie zostało dodane po wyznaczonym czasie"
    )
    like_count = models.IntegerField(default=0, help_text="Liczba polubień zdjęcia")
    view_count = models.IntegerField(default=0, help_text="Liczba wyświetleń zdjęcia")

    def __str__(self):
        return f"BeRealPhoto #{self.id} by {self.user.username}"


class BeRealPhotoInteraction(models.Model):
    INTERACTION_TYPES = (
        (1, "like"),
        (2, "view"),
    )
    photo = models.ForeignKey(
        BeRealPhoto,
        on_delete=models.CASCADE,
        related_name="interactions",
        help_text="Zdjęcie, z którym związana jest interakcja",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="photo_interactions",
        help_text="Użytkownik wykonujący akcję",
    )
    interaction_type = models.IntegerField(
        choices=INTERACTION_TYPES, help_text="Typ interakcji: like, view"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Data i godzina wykonania interakcji"
    )

    def __str__(self):
        return f"{self.get_interaction_type_display()} by {self.user.username} on photo #{self.photo.id}"


class BeRealNotification(models.Model):
    predicted_send_time = models.DateTimeField(
        help_text="Planowany czas wysłania powiadomienia"
    )
    is_sent = models.BooleanField(
        default=False, help_text="Czy powiadomienie zostało wysłane"
    )
    sent_at = models.DateTimeField(
        null=True, blank=True, help_text="Rzeczywisty czas wysłania powiadomienia"
    )

    def __str__(self):
        return f"Notification #{self.id} (sent: {self.is_sent})"


# class BeRealComment(models.Model):
#     photo = models.ForeignKey(BeRealPhoto, on_delete=models.CASCADE, related_name='comments', help_text="Zdjęcie, do którego dodano komentarz")
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bereal_comments', help_text="Użytkownik dodający komentarz")
#     comment_text = models.TextField(help_text="Treść komentarza")
#     created_at = models.DateTimeField(auto_now_add=True, help_text="Data i godzina dodania komentarza")

#     def __str__(self):
#         return f"Comment by {self.user.username} on photo #{self.photo.id}"
