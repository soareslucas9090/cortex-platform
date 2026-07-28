from django.apps import apps
from django.conf import settings

from AppCore.core.rules.rules import ModelInstanceRules

from Infraestrutura.permissoes.access import usuario_pode_operar_infraestrutura


class EmprestimoRules(ModelInstanceRules):

    def pode_operar(self, conta_autenticada) -> bool:
        """Operações de empréstimo exigem capacidade operar na conta autenticada."""
        if not usuario_pode_operar_infraestrutura(conta_autenticada):
            self.return_exception('Você não tem permissão para operar empréstimos.')
        return True

    def resolver_responsavel(self, conta_autenticada, responsavel_id=None):
        """Define o responsável (quem entrega o recurso) conforme o tipo de conta."""
        from Identidade.usuarios.models import Usuario

        if not conta_autenticada.usuario_coletivo:
            if responsavel_id is not None and responsavel_id != conta_autenticada.pk:
                self.return_exception(
                    'Não é permitido informar outro responsável para esta conta.',
                )
            conta_autenticada.rules.conta_coletiva_nao_participa_emprestimo()
            return conta_autenticada

        if not responsavel_id:
            self.return_exception('Informe o responsável pelo empréstimo.')

        pool = Usuario().helper.listar_responsaveis_do_coletivo(conta_autenticada)
        responsavel = pool.filter(pk=responsavel_id).first()
        if responsavel is None:
            self.return_exception('Responsável informado não é elegível para esta conta.')
        return responsavel

    def validar_solicitante_ativo(self, solicitante_id: int) -> bool:
        Usuario = apps.get_model(settings.AUTH_USER_MODEL)
        solicitante = Usuario.objects.filter(pk=solicitante_id).first()
        if solicitante is None:
            self.return_exception('Solicitante informado não encontrado.')
        if not solicitante.ativo:
            self.return_exception('O solicitante informado está inativo.')
        if solicitante.usuario_coletivo:
            self.return_exception('Conta coletiva não pode ser solicitante de empréstimo.')
        return True

    def validar_recursos_informados(self, recurso_ids: list, recursos) -> bool:
        if not recurso_ids:
            self.return_exception('Informe ao menos um recurso para o empréstimo.')
        ids_encontrados = {recurso.pk for recurso in recursos}
        if len(ids_encontrados) != len(set(recurso_ids)):
            self.return_exception('Um ou mais recursos informados não foram encontrados.')
        return True

    def validar_recurso_disponivel(self, recurso) -> bool:
        if not recurso.ativo:
            self.return_exception(f'O recurso {recurso.codigo} está inativo.')
        if recurso.em_avaria:
            self.return_exception(f'O recurso {recurso.codigo} está em avaria.')
        if self.object_instance.helper.recurso_esta_emprestado(recurso):
            self.return_exception(f'O recurso {recurso.codigo} já possui empréstimo em aberto.')
        return True

    def validar_elegibilidade_solicitante_para_recurso(self, solicitante, recurso) -> bool:
        if not self.object_instance.helper.solicitante_pode_retirar_recurso(solicitante, recurso):
            self.return_exception(
                f'O solicitante não possui autorização para retirar o recurso {recurso.codigo}.',
            )
        return True

    def pode_devolver_itens(self) -> bool:
        if not self.object_instance.helper.esta_ativo():
            self.return_exception('O empréstimo já está encerrado.')
        return True

    def validar_itens_para_devolucao(self, itens, item_ids: list) -> bool:
        if not item_ids:
            self.return_exception('Informe ao menos um item para devolução.')
        ids_encontrados = {item.pk for item in itens}
        if len(ids_encontrados) != len(set(item_ids)):
            self.return_exception('Um ou mais itens informados não pertencem a este empréstimo.')
        for item in itens:
            if item.devolvido_em is not None:
                self.return_exception(f'O item do recurso {item.recurso.codigo} já foi devolvido.')
        return True

    def pode_trocar_titular(self) -> bool:
        if not self.object_instance.itens.filter(devolvido_em__isnull=True).exists():
            self.return_exception('Não há itens em aberto para troca de titular.')
        return True

    def pode_consultar(self, usuario) -> bool:
        if not self.object_instance.helper.usuario_pode_consultar_emprestimo(
            usuario,
            self.object_instance,
        ):
            self.return_not_allowed()
        return True
