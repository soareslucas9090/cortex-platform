from AppCore.core.rules.rules import ModelInstanceRules


class PermissaoFuncaoTransporteRules(ModelInstanceRules):

    def funcao_deve_estar_ativa(self, funcao) -> bool:
        if not funcao.ativo:
            self.return_exception('Não é possível configurar permissões para uma função inativa.')
        return True

    def funcao_sem_permissao_existente(self, funcao_id: int) -> bool:
        from .models import PermissaoFuncaoTransporte
        if PermissaoFuncaoTransporte.objects.filter(funcao_id=funcao_id).exists():
            self.return_exception('Já existe permissão de Transporte para esta função.')
        return True
