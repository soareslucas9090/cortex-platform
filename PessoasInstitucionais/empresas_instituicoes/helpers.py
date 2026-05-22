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
