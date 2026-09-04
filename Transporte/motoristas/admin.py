from django.contrib import admin

from .models import Motorista


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'ativo', 'created_at']
    list_filter = ['ativo']
    search_fields = ['usuario__nome', 'usuario__cpf', 'usuario__email']
