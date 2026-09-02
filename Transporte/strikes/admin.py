from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import Strike


@admin.register(Strike)
class StrikeAdmin(ReadOnlyModelAdmin):
    list_display = ['id', 'ticket', 'status', 'created_at']
    list_filter = ['status']
