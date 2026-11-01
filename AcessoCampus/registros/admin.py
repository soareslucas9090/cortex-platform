from django.contrib import admin

from .models import RegistroAcesso


@admin.register(RegistroAcesso)
class RegistroAcessoAdmin(admin.ModelAdmin):
    list_display = ("evento", "resultado", "registrado_por", "operado_por", "registrado_em")
    list_filter = ("resultado", "registrado_em")
    search_fields = ("evento__aluno_nome", "registrado_por__nome", "operado_por__nome")
