from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .business import EmpresaInstituicaoBusiness
from .models import EmpresaInstituicao


@admin.register(EmpresaInstituicao)
class EmpresaInstituicaoAdmin(AtivoModelAdmin):
    list_display = ('nome', 'cnpj', 'ativo', 'created_at')
    search_fields = ('nome', 'cnpj')
    ordering = ('nome',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: EmpresaInstituicaoBusiness().criar_empresa(
                    {
                        'nome': obj.nome,
                        'cnpj': obj.cnpj,
                        'ativo': obj.ativo,
                    }
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
