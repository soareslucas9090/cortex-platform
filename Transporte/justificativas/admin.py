from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import Justificativa


@admin.register(Justificativa)
class JustificativaAdmin(ReadOnlyModelAdmin):
    list_display = ['id', 'strike', 'status', 'analisada_por', 'analisada_em']
    list_filter = ['status']
