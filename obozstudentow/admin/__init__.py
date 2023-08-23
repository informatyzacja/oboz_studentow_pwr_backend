from .group import *
from .meals import *
from .people import *
from .workshop import *
from .user import *

from import_export.admin import ImportExportModelAdmin

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import Link, FAQ, ScheduleItem, User, Icons


admin.site.site_header = "Panel administracyjny Obozu Studentów PWR 2023"
admin.site.site_title = "Panel administracyjny Obozu Studentów PWR 2023"
admin.site.index_title = "Witaj w panelu administracyjnym Obozu Studentów PWR 2023"

class LinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'icon')
    search_fields = ('name', 'url', 'icon')

class FAQAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'answer')

class ScheduleItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'description', 'start', 'end', 'location', 'visible', 'has_image')
    search_fields = ('name', 'description', 'start', 'end', 'location', 'visible')
    # filter_vertical = ('has_image',)
    ordering = ('start','end')

@admin.register(Icons)
class IconsAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name', 'icon')

admin.site.register(Link, LinkAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(ScheduleItem, ScheduleItemAdmin)
        
from ..models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'date', 'addedBy', 'group', 'visible')
    search_fields = ('title', 'content', 'date', 'addedBy', 'group', 'visible')

    def get_form(self, request, obj=None, **kwargs):
        form = super(AnnouncementAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['addedBy'].queryset = User.objects.filter(groups__name__in=('Kadra','Sztab','Bajer'))
        return form

from ..models import DailyQuest

@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'finish', 'addedBy', 'group', 'visible')
    search_fields = ('title', 'description', 'finish', 'addedBy', 'group', 'visible')

    def get_form(self, request, obj=None, **kwargs):
        form = super(DailyQuestAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['addedBy'].queryset = User.objects.filter(groups__name__in=('Sztab'))
        return form


from ..models import Bus

@admin.register(Bus)
class BusAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('description', 'location')
    search_fields = ('description', 'location')


from ..models import Image
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')
    search_fields = ('name', 'image')


from ..models import Setting
@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'value')
    search_fields = ('name', 'description', 'value')

from ..models import Partners
@admin.register(Partners)
class PartnersAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo', 'link')
    search_fields = ('name', 'logo', 'link')

from ..models import House
@admin.register(House)
class HouseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'key_collected')
    search_fields = ('name',)

    list_filter = ('key_collected',)