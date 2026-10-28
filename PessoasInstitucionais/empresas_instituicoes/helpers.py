from AppCore.core.helpers.helpers import ModelInstanceHelpers


class EmpresaInstituicaoHelpers(ModelInstanceHelpers):

    @property
    def eh_ativa(self) -> bool:
        """Verifica se a empresa está ativa."""
        return self.object_instance.ativo

    def get_cnpj_formatado(self) -> str:
        """Retorna o CNPJ formatado."""
        cnpj = self.object_instance.cnpj
        if not cnpj or len(cnpj) != 14:
            return cnpj
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'

    def obter_por_cnpj(self, cnpj):
        """Retorna empresa pelo CNPJ (dígitos), ignorando registros sem CNPJ."""
        from AppCore.common.util.util import normalizar_cnpj
        from .models import EmpresaInstituicao

        if not cnpj:
            return None
        for empresa in EmpresaInstituicao.objects.all():
            if empresa.cnpj and normalizar_cnpj(empresa.cnpj) == cnpj:
                return empresa
        return None

    def obter_por_nome_normalizado(self, nome):
        """Retorna empresa cujo nome coincide após normalização de texto, ou None."""
        from AppCore.common.util.util import normalizar_chave_texto
        from .models import EmpresaInstituicao

        chave = normalizar_chave_texto(nome)
        if not chave:
            return None
        for empresa in EmpresaInstituicao.objects.all():
            if normalizar_chave_texto(empresa.nome) == chave:
                return empresa
        return None
