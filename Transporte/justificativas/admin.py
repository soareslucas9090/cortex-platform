from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import Justificativa


@admin.register(Justificativa)
class JustificativaAdmin(ReadOnlyModelAdmin):
    list_display = ['id', 'aluno', 'status', 'analisada_por', 'analisada_em']
    list_filter = ['status']
