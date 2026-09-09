from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import DiaCalendarioTransporte


@admin.register(DiaCalendarioTransporte)
class DiaCalendarioTransporteAdmin(AtivoModelAdmin):
    list_display = ('data', 'descricao', 'tipo', 'ativo')
    list_filter = ('ativo', 'tipo')
    search_fields = ('descricao',)
    ordering = ('data',)

    def save_model(self, request, obj, form, change):
        if not change:
            criado = run_business(
                lambda: DiaCalendarioTransporte().business.criar_dia(
                    data=obj.data,
                    descricao=obj.descricao,
                    tipo=obj.tipo,
                    ativo=obj.ativo,
                )
            )
            obj.pk = criado.pk
            return

        dados = {
            campo: form.cleaned_data[campo]
            for campo in form.changed_data
        }
        ativo_novo = dados.pop('ativo', None)
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
        if ativo_novo is not None:
            obj.refresh_from_db()
            if ativo_novo:
                run_business(lambda: obj.business.reativar())
            else:
                run_business(lambda: obj.business.desativar())
