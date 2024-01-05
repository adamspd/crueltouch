from django.contrib import admin
from django.contrib.auth import get_user_model

from client.models import Album, BookMe, OwnerProfilePhoto, Photo, UserClient


# class InlinePhoto(admin.TabularInline):
#     model = Photo


# class InlineBook(admin.TabularInline):
#     model = BookMe
#     extra = 1


# class PhotoAdmin(admin.ModelAdmin):
#     list_display = ('owner', 'is_favorite', 'can_be_downloaded', 'file')
#     actions = ('make_favorite', 'remove_favorite', 'can_be_downloaded', 'cant_be_downloaded')
#
#     def make_favorite(self, request, queryset):
#         count = queryset.update(is_favorite=True)
#         self.message_user(request, "{} photos have been made favorite".format(count))
#
#     make_favorite.short_description = 'Make Photos Favorite'
#
#     def remove_favorite(self, request, queryset):
#         count = queryset.update(is_favorite=False)
#         self.message_user(request, "{} photos have been removed from favorite".format(count))
#
#     remove_favorite.short_description = 'Remove Photos From Favorite'
#
#     def can_be_downloaded(self, request, queryset):
#         count = queryset.update(can_be_downloaded=True)
#         self.message_user(request, "{} photos can be downloaded".format(count))
#
#     can_be_downloaded.short_description = 'Can Be Downloaded'
#
#     def cant_be_downloaded(self, request, queryset):
#         count = queryset.update(cant_be_downloaded=False)
#         self.message_user(request, "{} photos can't be downloaded".format(count))
#
#     cant_be_downloaded.short_description = "Can't Be Downloaded"
#
#

class BookMeConfig(admin.ModelAdmin):
    model = BookMe
    search_fields = ('full_name', 'email', 'time_book_taken')
    list_filter = ('time_book_taken', 'full_name', 'status', 'package')
    ordering = ('-time_book_taken',)
    list_display = ('full_name', 'time_book_taken', 'package', 'session_type', 'place')


@admin.register(UserClient)
class UserClientAdmin(admin.ModelAdmin):
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('first_name', 'last_name', 'email')
    ordering = ('first_name',)
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'is_active', 'is_staff', 'is_superuser')


User = get_user_model()
admin.site.register(BookMe, BookMeConfig)
admin.site.register(Album)
admin.site.register(Photo)
admin.site.register(OwnerProfilePhoto)
