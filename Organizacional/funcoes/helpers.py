from AppCore.core.helpers.helpers import ModelInstanceHelpers


class FuncaoHelpers(ModelInstanceHelpers):

    # ------------------------------------------------------------------
    # Consultas de instância (operam sobre self.object_instance = Funcao)
    # ------------------------------------------------------------------

    def esta_em_uso(self) -> bool:
        """Verifica se a função está associada a algum vínculo."""
        return self.object_instance.vinculos.exists()

    def obter_vinculos(self):
        """Retorna todos os vínculos que utilizam esta função."""
        return self.object_instance.vinculos.all()

    # ------------------------------------------------------------------
    # Consultas globais do domínio
    # ------------------------------------------------------------------

    def listar_ativas(self):
        """Retorna todas as funções ativas."""
        from .models import Funcao
        return Funcao.objects.filter(ativo=True)

    def listar_inativas(self):
        """Retorna todas as funções inativas."""
        from .models import Funcao
        return Funcao.objects.filter(ativo=False)

    def obter_por_papel_funcao_normalizado(self, papel_funcao):
        """Retorna a função cujo papel coincide após normalização de texto, ou None."""
        from AppCore.common.util.util import normalizar_chave_texto
        from .models import Funcao

        chave = normalizar_chave_texto(papel_funcao)
        if not chave:
            return None
        for funcao in Funcao.objects.all():
            if normalizar_chave_texto(funcao.papel_funcao) == chave:
                return funcao
        return None

    def resolver_categoria_funcao(self, categoria):
        """Resolve categoria pelo valor ou label; padrão coordenador; None se inválida."""
        from AppCore.common.util.util import normalizar_chave_texto
        from .choices import CategoriaFuncao

        if not (categoria or '').strip():
            return CategoriaFuncao.COORDENADOR

        chave = normalizar_chave_texto(categoria)
        for valor, label in CategoriaFuncao.choices:
            if normalizar_chave_texto(valor) == chave or normalizar_chave_texto(label) == chave:
                return valor
        return None
