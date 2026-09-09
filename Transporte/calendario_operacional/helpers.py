from AppCore.core.helpers.helpers import ModelInstanceHelpers


class DiaCalendarioTransporteHelpers(ModelInstanceHelpers):

    def obter_excecao_ativa_na_data(self, data):
        from .models import DiaCalendarioTransporte

        return DiaCalendarioTransporte.objects.filter(
            data=data,
            ativo=True,
        ).first()
