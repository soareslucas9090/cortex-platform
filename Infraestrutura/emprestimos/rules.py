from django.apps import apps
from django.conf import settings

from AppCore.core.rules.rules import ModelInstanceRules
from Infraestrutura.permissoes.access import usuario_pode_operar_infraestrutura

from .choices import OrigemContaColetiva, StatusSolicitacaoTrocaTitular


class EmprestimoRules(ModelInstanceRules):

    def pode_listar_destinatarios_troca(self, conta_autenticada, recursos_pertencem_a_emprestimo_proprio: bool) -> bool:
        if conta_autenticada.usuario_coletivo:
            self.return_not_allowed('Conta coletiva deve utilizar o fluxo administrativo de troca de titular.')
        if not conta_autenticada.ativo:
            self.return_not_allowed('O usuário autenticado está inativo.')
        if not recursos_pertencem_a_emprestimo_proprio:
            self.return_not_allowed('Você não pode consultar destinatários para estes recursos.')
        return True

    def pode_operar(self, conta_autenticada) -> bool:
        """Operações de empréstimo exigem capacidade operar na conta autenticada."""
        if not usuario_pode_operar_infraestrutura(conta_autenticada):
            self.return_exception('Você não tem permissão para operar empréstimos.')
        return True

    def resolver_origem_conta_coletiva(self, conta_autenticada):
        """Congela a origem da operação a partir da conta autenticada."""
        if not conta_autenticada.usuario_coletivo:
            return None
        tipo = conta_autenticada.tipo_conta_coletiva
        if tipo not in OrigemContaColetiva.values:
            self.return_exception('A conta coletiva precisa ter um tipo válido para operar empréstimos.')
        return tipo

    def resolver_responsavel(self, conta_autenticada, responsavel_id=None):
        """Define o responsável (quem entrega o recurso) conforme o tipo de conta."""
        from Identidade.usuarios.models import Usuario

        if not conta_autenticada.usuario_coletivo:
            if responsavel_id is not None and responsavel_id != conta_autenticada.pk:
                self.return_exception('Não é permitido informar outro responsável para esta conta.')
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
        if len(recurso_ids) != len(set(recurso_ids)):
            self.return_exception('IDs de recurso duplicados.')
        ids_encontrados = {recurso.pk for recurso in recursos}
        if len(ids_encontrados) != len(set(recurso_ids)):
            self.return_exception('Um ou mais recursos informados não foram encontrados.')
        return True

    def validar_recurso_disponivel(self, recurso, possui_emprestimo_aberto: bool) -> bool:
        if not recurso.ativo:
            self.return_exception(f'O recurso {recurso.codigo} está inativo.')
        if recurso.em_avaria:
            self.return_exception(f'O recurso {recurso.codigo} está em avaria.')
        if possui_emprestimo_aberto:
            identificacao = recurso.codigo
            if recurso.sala_id:
                identificacao = f'{recurso.sala.nome} / {recurso.sala.bloco.nome}'
            self.return_exception(f'O recurso {identificacao} já possui empréstimo em aberto.')
        return True

    def validar_elegibilidade_solicitante_para_recurso(self, solicitante, recurso) -> bool:
        if not self.object_instance.helper.solicitante_pode_retirar_recurso(solicitante, recurso):
            self.return_exception(f'O solicitante não possui autorização para retirar o recurso {recurso.codigo}.')
        return True

    def pode_devolver_itens(self) -> bool:
        if not self.object_instance.helper.esta_ativo():
            self.return_exception('O empréstimo já está encerrado.')
        return True

    def validar_itens_para_devolucao(self, itens, item_ids: list) -> bool:
        if not item_ids:
            self.return_exception('Informe ao menos um item para devolução.')
        if len(item_ids) != len(set(item_ids)):
            self.return_exception('IDs de item duplicados.')
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

    def validar_consulta(self, permitido: bool) -> bool:
        if not permitido:
            self.return_not_allowed('Você não tem permissão para consultar este empréstimo.')
        return True


class SolicitacaoTrocaTitularRules(ModelInstanceRules):

    def validar_solicitante(self, usuario, emprestimo) -> bool:
        if usuario.usuario_coletivo:
            self.return_exception('Conta coletiva não pode solicitar troca de titular.')
        if not usuario.ativo:
            self.return_exception('O usuário solicitante está inativo.')
        if emprestimo.solicitante_id != usuario.pk:
            self.return_not_allowed('Somente o titular atual do empréstimo pode solicitar a troca.')
        return True

    def validar_emprestimo_aberto(self, possui_itens_abertos: bool) -> bool:
        if not possui_itens_abertos:
            self.return_exception('O empréstimo já está encerrado.')
        return True

    def validar_destinatario(self, destinatario, servidor_ativo: bool) -> bool:
        if destinatario is None:
            self.return_exception('Destinatário informado não encontrado.')
        if not destinatario.ativo:
            self.return_exception('O destinatário informado está inativo.')
        if destinatario.usuario_coletivo:
            self.return_exception('Conta coletiva não pode receber troca de titular.')
        if not servidor_ativo:
            self.return_exception('O destinatário deve possuir perfil de servidor ativo.')
        return True

    def validar_destinatario_diferente(self, destinatario_id: int, titular_id: int) -> bool:
        if destinatario_id == titular_id:
            self.return_exception('Não é permitido solicitar troca de titular para si mesmo.')
        return True

    def validar_sem_solicitacao_pendente(self, possui_pendente: bool) -> bool:
        if possui_pendente:
            self.return_exception('Já existe uma solicitação de troca pendente para o empréstimo.')
        return True

    def validar_elegibilidade_destinatario(self, elegivel: bool, codigo_recurso: str) -> bool:
        if not elegivel:
            self.return_exception(f'O destinatário não é elegível para o recurso {codigo_recurso}.')
        return True

    def validar_pendente(self) -> bool:
        if self.object_instance.status != StatusSolicitacaoTrocaTitular.PENDENTE:
            self.return_exception('A solicitação já foi processada.')
        return True

    def pode_aceitar(self, usuario) -> bool:
        if self.object_instance.destinatario_id != usuario.pk:
            self.return_not_allowed('Somente o destinatário pode aceitar a solicitação.')
        return True

    def pode_recusar(self, usuario) -> bool:
        if self.object_instance.destinatario_id != usuario.pk:
            self.return_not_allowed('Somente o destinatário pode recusar a solicitação.')
        return True

    def pode_cancelar(self, usuario) -> bool:
        if self.object_instance.solicitante_id != usuario.pk:
            self.return_not_allowed('Somente o solicitante pode cancelar a solicitação.')
        return True
