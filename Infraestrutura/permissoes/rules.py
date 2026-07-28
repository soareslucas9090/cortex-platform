from AppCore.core.rules.rules import ModelInstanceRules


class PermissaoFuncaoInfraestruturaRules(ModelInstanceRules):

    def funcao_deve_estar_ativa(self, funcao) -> bool:
        """Permissão só pode ser vinculada a função ativa."""
        if not funcao.ativo:
            self.return_exception('Não é possível configurar permissões para uma função inativa.')
        return True

    def funcao_sem_permissao_existente(self, funcao_id: int) -> bool:
        """Garante unicidade da configuração por função."""
        from .models import PermissaoFuncaoInfraestrutura
        if PermissaoFuncaoInfraestrutura.objects.filter(funcao_id=funcao_id).exists():
            self.return_exception('Já existe permissão de Infraestrutura para esta função.')
        return True


class PermissaoUsuarioInfraestruturaRules(ModelInstanceRules):

    def usuario_deve_estar_ativo(self, usuario) -> bool:
        """Permissão só pode ser vinculada a usuário ativo."""
        if not usuario.ativo:
            self.return_exception('Não é possível configurar permissões para um usuário inativo.')
        return True

    def usuario_sem_permissao_existente(self, usuario_id: int) -> bool:
        """Garante unicidade da configuração por usuário."""
        from .models import PermissaoUsuarioInfraestrutura
        if PermissaoUsuarioInfraestrutura.objects.filter(usuario_id=usuario_id).exists():
            self.return_exception('Já existe permissão de Infraestrutura para este usuário.')
        return True
