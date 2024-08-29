from django.http.request import HttpRequest
from .group import *
from .meals import *
from .people import *
from .workshop import *
from .user import *

from import_export.admin import ImportExportModelAdmin

from orderable.admin import OrderableAdmin

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import Link, FAQ, ScheduleItem, User, Icons, HomeLink



class LinkAdmin(OrderableAdmin):
    list_display = ('name', 'url', 'icon', 'sort_order_display')
    search_fields = ('name', 'url', 'icon')

@admin.register(HomeLink)
class HomeLinkAdmin(OrderableAdmin):
    list_display = ('name', 'url', 'image', 'icon', 'visible', 'sort_order_display')
    search_fields = ('name', 'url', 'icon')

class FAQAdmin(ImportExportModelAdmin, OrderableAdmin):
    list_display = ('question', 'answer', 'sort_order_display')
    search_fields = ('question', 'answer')


@admin.action(description='Ukryj mapki')
def hide_maps(modeladmin, request, queryset):
    queryset.update(hide_map=True)

@admin.action(description='Pokaż mapki')
def show_maps(modeladmin, request, queryset):
    queryset.update(hide_map=False)

class ScheduleItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'description', 'start', 'end', 'location', 'visible', 'has_image')
    search_fields = ('name', 'description', 'start', 'end', 'location', 'visible')
    # filter_vertical = ('has_image',)
    ordering = ('start','end')

    actions = [hide_maps, show_maps]

@admin.register(Icons)
class IconsAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name', 'icon')

admin.site.register(Link, LinkAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(ScheduleItem, ScheduleItemAdmin)
        
from ..models import Announcement

@admin.action(description='Ukryj')
def hide_announncements(modeladmin, request, queryset):
    queryset.update(visible=False)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'date', 'addedBy', 'group', 'visible')
    search_fields = ('title', 'content', 'date', 'addedBy', 'group', 'visible')

    def get_form(self, request, obj=None, **kwargs):
        form = super(AnnouncementAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['addedBy'].queryset = User.objects.filter(groups__name__in=('Kadra','Sztab','Bajer'))
        return form
    
    actions = [hide_announncements]

from ..models import DailyQuest

@admin.register(DailyQuest)
class DailyQuestAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('title', 'description', 'start', 'finish', 'group', 'visible')
    search_fields = ('title', 'description', 'start', 'finish', 'group__name', 'visible')


from ..models import Bus

@admin.register(Bus)
class BusAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('__str__', 'user_count_to', 'user_count_return', 'location')
    search_fields = ('__str__', 'description', 'location')

    def user_count_to(self, obj):
        return obj.user_set.filter(bus_info__in=(User.BusInfoChoices.BOTH, User.BusInfoChoices.TO)).count()
    user_count_to.short_description = 'Liczba użytkowników w tamtą stronę'

    def user_count_return(self, obj):
        return obj.user_set.filter(bus_info__in=(User.BusInfoChoices.BOTH, User.BusInfoChoices.RETURN)).count()
    user_count_return.short_description = 'Liczba użytkowników w powrotną stronę'


from ..models import Image
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'visible')
    search_fields = ('name', 'image')
    list_filter = ('visible',)


from ..models import Setting
@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'value')
    search_fields = ('name', 'description', 'value')
    readonly_fields = ('name', 'description')

from ..models import Partners
@admin.register(Partners)
class PartnersAdmin(OrderableAdmin):
    list_display = ('name', 'logo', 'link', 'sort_order_display')
    search_fields = ('name', 'logo', 'link')




from ..models import House
class HouseMemberInline(admin.TabularInline):
    model = User
    extra = 0
    # autocomplete_fields = ('person',)
    verbose_name = "Lokator"
    verbose_name_plural = "Lokatorzy"
    fields = ('first_name', 'last_name', 'email', 'bandId')
    readonly_fields = ('first_name', 'last_name', 'email', 'bandId', 'chat')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False



@admin.action(description='Otwórz zapisy')
def open_signup(modeladmin, request, queryset):
    queryset.update(signup_open=True)

@admin.action(description='Zamknij zapisy')
def close_signup(modeladmin, request, queryset):
    queryset.update(signup_open=False)

@admin.action(description='Otwórz wypisy')
def open_signout(modeladmin, request, queryset):
    queryset.update(signout_open=True)

@admin.action(description='Zamknij wypisy')
def close_signout(modeladmin, request, queryset):
    queryset.update(signout_open=False)


@admin.register(House)
class HouseAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'key_collected', 'locators', 'places', 'full', 'floor')
    search_fields = ('name','floor', 'user__first_name', 'user__last_name', 'user__email')

    list_filter = ('key_collected','floor')

    inlines = [HouseMemberInline]

    actions = [open_signup, close_signup, open_signout, close_signout]

class HouseView(House):
    class Meta:
        proxy = True
        verbose_name = "Pokój/domek (widok)"
        verbose_name_plural = "Pokoje/domki (widok)"
        ordering = ('floor', 'name')

@admin.register(HouseView)
class HouseViewAdmin(admin.ModelAdmin):
    list_display = ('name', 'key_collected', 'locators', 'places', 'full', 'floor', 'signup_open', 'signout_open')
    search_fields = ('name','floor', 'user__first_name', 'user__last_name', 'user__email')

    readonly_fields = ('name', 'locators', 'places', 'full', 'floor', 'description', 'chat')

    list_filter = ('key_collected','floor', 'places', 'signup_open', 'signout_open')

    inlines = [HouseMemberInline]

    actions = [open_signup, close_signup, open_signout, close_signout]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(HouseViewAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user_key_collected'].queryset = User.objects.filter(house=obj)
        return form
    