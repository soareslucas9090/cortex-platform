from AppCore.core.rules.rules import ModelInstanceRules


class PermissaoFuncaoTransporteRules(ModelInstanceRules):

    def validar_funcao_ativa(self, funcao) -> bool:
        if not funcao.ativo:
            self.return_exception('Não é possível configurar permissões para uma função inativa.')
        return True

    def validar_funcao_sem_permissao(self, ja_existe) -> bool:
        if ja_existe:
            self.return_exception('Já existe permissão de Transporte para esta função.')
        return True


class PermissaoUsuarioTransporteRules(ModelInstanceRules):

    def validar_usuario_ativo(self, usuario) -> bool:
        if not usuario.ativo:
            self.return_exception('Não é possível configurar permissões para um usuário inativo.')
        return True

    def validar_usuario_sem_permissao(self, ja_existe) -> bool:
        if ja_existe:
            self.return_exception('Já existe permissão de Transporte para este usuário.')
        return True
