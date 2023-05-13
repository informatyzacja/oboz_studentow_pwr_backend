from django.db import models

class GroupType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100)
    type = models.ForeignKey(GroupType, on_delete=models.PROTECT)
    logo = models.ImageField(upload_to='groups', blank=True)
    map = models.ImageField(upload_to='groups/maps', blank=True)
    messenger = models.URLField(blank=True)
    
    def __str__(self):
        return self.name
    
class GroupMember(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.group.name + ")"
    
class GroupWarden(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.group.name + ")"


# points
class PointType(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class Point(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    type = models.ForeignKey(PointType, blank=True, null=True, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    addedBy = models.ForeignKey('obozstudentow.User', on_delete=models.SET_NULL, null=True)
    numberOfPoints = models.FloatField()

# announcements
class Announcement(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=100)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    addedBy = models.ForeignKey('obozstudentow.User', on_delete=models.SET_NULL, null=True)
    visible = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title