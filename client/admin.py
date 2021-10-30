from django.contrib import admin
from django.template.defaulttags import csrf_token

from .models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model


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
# class UserAdminConfig(admin.ModelAdmin):
#     model = UserClient
#     inlines = [
#         InlinePhoto,
#         # InlineBook
#     ]
#     search_fields = ('email', 'first_name',)
#     list_filter = ('email', 'first_name', 'active', 'staff')
#     ordering = ('-start_date',)
#     list_display = ('first_name', 'email',
#                     'active', 'admin')
#     fieldsets = (
#         (None, {'fields': ('email', 'first_name',)}),
#         ('CAN LOGIN', {'fields': ('active',)}),
#         # ('Personal', {'fields': ('about',)}),
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'first_name', 'password1', 'password2', 'active', 'staff')}
#          ),
#     )


User = get_user_model()
# Register your models here.
# admin.site.register(Photo, PhotoAdmin)
# admin.site.register(UserClient, UserAdminConfig)
admin.site.register(BookMe)
admin.site.register(Album)
admin.site.register(Photo)
admin.site.register(OwnerProfilePhoto)
