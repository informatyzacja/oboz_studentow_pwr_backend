from django.db import models
from django_resized import ResizedImageField
from obozstudentow_async.models import Chat

class GroupType(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Rodzaj grupy"
        verbose_name_plural = "Rodzaje grup"

    def __str__(self):
        return self.name
    
from orderable.models import Orderable

class Group(Orderable):
    name = models.CharField(max_length=100)
    type = models.ForeignKey(GroupType, on_delete=models.PROTECT)
    logo = models.FileField(upload_to='groups', blank=True, null=True)
    map = ResizedImageField(upload_to='groups/maps', blank=True, null=True)
    background = models.ImageField(upload_to='groups/backgrounds', blank=True, null=True)
    messenger = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    chat = models.ForeignKey(Chat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Czat")

    class Meta(Orderable.Meta):
        verbose_name = "Grupa"
        verbose_name_plural = "Grupy"
    
    def __str__(self):
        return self.name + " (" + self.type.name + ")"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.chat:
            self.chat = Chat.objects.create(name=self.name)
            self.chat.users.add(*self.groupmember_set.values_list('user', flat=True))
            self.chat.users.add(*self.groupwarden_set.values_list('user', flat=True))
            self.save()
    
class GroupMember(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Członek grupy"
        verbose_name_plural = "Członkowie grupy"

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.group.name + ")"
    
    def __save__(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # add user to group chat
        if self.group.chat and not self.group.chat.users.filter(pk=self.user.pk).exists():
            self.group.chat.users.add(self.user)

    def __delete__(self, *args, **kwargs):
        # remove user from group chat
        if self.group.chat and self.group.chat.users.filter(pk=self.user.pk).exists():
            self.group.chat.users.remove(self.user)
            
        super().delete(*args, **kwargs)

    
class GroupWarden(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Opiekun grupy"
        verbose_name_plural = "Opiekunowie grupy"

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.group.name + ")"
        

    def __save__(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # add user to group chat
        if self.group.chat and not self.group.chat.users.filter(pk=self.user.pk).exists():
            self.group.chat.users.add(self.user)

    def __delete__(self, *args, **kwargs):
        # remove user from group chat
        if self.group.chat and self.group.chat.users.filter(pk=self.user.pk).exists():
            self.group.chat.users.remove(self.user)
            
        super().delete(*args, **kwargs)



# points
class PointType(models.Model):
    name = models.CharField(max_length=100)
    group_type = models.ForeignKey(GroupType, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    points_max = models.FloatField()
    points_min = models.FloatField(default = 0)


    class Meta:
        verbose_name = "Rodzaj punktu"
        verbose_name_plural = "Rodzaje punktów"
    
    def __str__(self):
        return self.name
    
class Point(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    type = models.ForeignKey(PointType, blank=True, null=True, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    addedBy = models.ForeignKey('obozstudentow.User', on_delete=models.SET_NULL, null=True)
    numberOfPoints = models.FloatField()

    validated = models.BooleanField(default=False)
    validatedBy = models.ForeignKey('obozstudentow.User', on_delete=models.SET_NULL, null=True, related_name="validatedBy")
    validationDate = models.DateTimeField(blank=True, null=True)
    rejected = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Punkty"
        verbose_name_plural = "Punkty"

# announcements
class Announcement(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=100)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    hide_date = models.DateTimeField(blank=True, null=True)
    addedBy = models.ForeignKey('obozstudentow.User', on_delete=models.SET_NULL, null=True)
    visible = models.BooleanField(default=True)


    class Meta:
        verbose_name = "Ogłoszenie"
        verbose_name_plural = "Ogłoszenia"
    
    def __str__(self):
        return self.title
    
class DailyQuest(models.Model):
    title = models.CharField(max_length=200)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(null=True, blank=True)

    start = models.DateTimeField(null=True, blank=True)
    finish = models.DateTimeField(null=True, blank=True)

    points = models.FloatField(null=True, blank=True)
    visible = models.BooleanField(default=True)


    class Meta:
        verbose_name_plural = "Daily questy"
    
    def __str__(self):
        return self.title
    

class NightGameSignup(models.Model):
    user_band = models.CharField(max_length=10)
    user_first_name = models.CharField(max_length=150)
    user_last_name = models.CharField(max_length=150)

    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    addedBy = models.ForeignKey('obozstudentow.User', on_delete=models.SET_NULL, null=True, related_name="addedBy")

    failed = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Zapis na grę nocną"
        verbose_name_plural = "Zapisy na grę nocną"

    def __str__(self):
        return self.user_first_name + " " + self.user_last_name