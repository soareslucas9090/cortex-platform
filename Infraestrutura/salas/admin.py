from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Sala, SalaSetor


@admin.register(Sala)
class SalaAdmin(AtivoModelAdmin):
    list_display = ('nome', 'bloco', 'ativo', 'created_at')
    list_filter = ('bloco', 'ativo')
    search_fields = ('nome', 'bloco__nome')
    ordering = ('bloco', 'nome')

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Sala().business.criar_sala(
                    bloco_id=obj.bloco_id,
                    nome=obj.nome,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))


@admin.register(SalaSetor)
class SalaSetorAdmin(admin.ModelAdmin):
    list_display = ('sala', 'setor', 'created_at')
    list_filter = ('setor',)
    search_fields = ('sala__nome', 'setor__nome', 'setor__sigla')
    ordering = ('sala', 'setor')

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: SalaSetor().business.criar_vinculo(
                    sala_id=obj.sala_id,
                    setor_id=obj.setor_id,
                )
            )
            obj.pk = created.pk
