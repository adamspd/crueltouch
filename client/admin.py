# client/admin.py
from django.contrib import admin

from client.models import Album, OwnerProfilePhoto, Photo, UserClient


@admin.register(UserClient)
class UserClientAdmin(admin.ModelAdmin):
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('first_name',)
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'is_staff', 'is_superuser', 'is_active')
    readonly_fields = ('last_login', 'start_date')


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('owner', 'is_active', 'was_viewed', 'created_at')
    list_filter = ('is_active', 'was_viewed')
    search_fields = ('owner__email', 'owner__first_name')


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_favorite', 'can_be_downloaded', 'file')
    list_filter = ('is_favorite', 'can_be_downloaded')
    actions = ['make_favorite', 'remove_favorite', 'set_downloadable', 'set_not_downloadable']

    @admin.action(description='Mark as favorite')
    def make_favorite(self, request, queryset):
        updated = queryset.update(is_favorite=True)
        self.message_user(request, f'{updated} photos marked as favorite')

    @admin.action(description='Remove from favorites')
    def remove_favorite(self, request, queryset):
        updated = queryset.update(is_favorite=False)
        self.message_user(request, f'{updated} photos removed from favorites')

    @admin.action(description='Set as downloadable')
    def set_downloadable(self, request, queryset):
        updated = queryset.update(can_be_downloaded=True)
        self.message_user(request, f'{updated} photos set as downloadable')

    @admin.action(description='Set as not downloadable')
    def set_not_downloadable(self, request, queryset):
        updated = queryset.update(can_be_downloaded=False)
        self.message_user(request, f'{updated} photos set as not downloadable')


admin.site.register(OwnerProfilePhoto)
