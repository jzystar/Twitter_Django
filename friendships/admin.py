from django.contrib import admin
from friendships.models import Friendship


@admin.register(Friendship)
class Friendship(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'from_user',
        'to_user',
        'created_at'
    )