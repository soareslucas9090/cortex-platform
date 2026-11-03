from AppCore.core.helpers.helpers import ModelInstanceHelpers


class TipoAutorizacaoAcessoHelpers(ModelInstanceHelpers):

    def listar(self):
        from .models import TipoAutorizacaoAcesso

        return TipoAutorizacaoAcesso.objects.all()

    def listar_ativos(self):
        from .models import TipoAutorizacaoAcesso

        return TipoAutorizacaoAcesso.objects.filter(ativo=True)

    def obter_por_id(self, tipo_id):
        from .models import TipoAutorizacaoAcesso

        return TipoAutorizacaoAcesso.objects.get(pk=tipo_id)

    def obter_por_nome(self, nome):
        from .models import TipoAutorizacaoAcesso

        return TipoAutorizacaoAcesso.objects.get(nome=nome)
