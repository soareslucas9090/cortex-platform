import logging

from django.apps import apps
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException

from Infraestrutura.permissoes.access import usuario_pode_operar_infraestrutura

from .choices import StatusSolicitacaoTrocaTitular

logger = logging.getLogger(__name__)


class EmprestimoBusiness(ModelInstanceBusiness):

    def listar_solicitantes_elegiveis(self, conta_autenticada, valores_recurso_ids, valores_recurso_id, nome=None):
        try:
            Recurso = apps.get_model('recursos', 'Recurso')
            recurso_ids = self.object_instance.helper.extrair_ids_recursos(valores_recurso_ids, valores_recurso_id)
            recursos = list(Recurso.objects.filter(pk__in=recurso_ids).select_related('sala'))
            self.object_instance.rules.validar_recursos_informados(recurso_ids, recursos)
            elegiveis = self.object_instance.helper.listar_solicitantes_elegiveis_para_recursos(recursos, nome=nome)
            if usuario_pode_operar_infraestrutura(conta_autenticada):
                return elegiveis

            recursos_proprios = self.object_instance.helper.recursos_pertencem_a_emprestimo_aberto_do_usuario(
                conta_autenticada, recurso_ids
            )
            self.object_instance.rules.pode_listar_destinatarios_troca(conta_autenticada, recursos_proprios)
            return elegiveis.filter(servidor__ativo=True).exclude(pk=conta_autenticada.pk)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os solicitantes elegíveis.', logger)

    def obter_detalhado(self, emprestimo_id: int):
        try:
            return self.object_instance.helper.obter_detalhado(emprestimo_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível consultar o empréstimo.', logger)

    def listar_detalhados(self, usuario=None):
        try:
            return self.object_instance.helper.listar_detalhados(usuario=usuario)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os empréstimos.', logger)

    def listar_para_usuario(self, usuario, **filtros):
        try:
            return self.object_instance.helper.listar_para_usuario(usuario, **filtros)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os empréstimos.', logger)

    def verificar_consulta(self, usuario):
        try:
            permitido = self.object_instance.helper.usuario_pode_consultar_emprestimo(usuario, self.object_instance)
            self.object_instance.rules.validar_consulta(permitido)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível consultar o empréstimo.', logger)

    def criar_emprestimo_validado(
        self,
        solicitante_id: int,
        responsavel,
        recurso_ids: list,
        observacao: str = '',
        retirada_em=None,
        origem_conta_coletiva=None,
    ):
        """Cria empréstimo após a autorização do fluxo chamador."""
        try:
            from .models import Emprestimo, ItemEmprestimo

            Recurso = apps.get_model('recursos', 'Recurso')
            Usuario = apps.get_model(settings.AUTH_USER_MODEL)
            recursos = list(
                Recurso.objects.select_for_update(of=('self',))
                .filter(pk__in=recurso_ids)
                .select_related('sala', 'sala__bloco')
            )
            self.object_instance.rules.validar_recursos_informados(recurso_ids, recursos)
            self.object_instance.rules.validar_solicitante_ativo(solicitante_id)
            solicitante = Usuario.objects.get(pk=solicitante_id)
            for recurso in recursos:
                self.object_instance.rules.validar_recurso_disponivel(
                    recurso, possui_emprestimo_aberto=(self.object_instance.helper.recurso_esta_emprestado(recurso))
                )
                self.object_instance.rules.validar_elegibilidade_solicitante_para_recurso(solicitante, recurso)
            momento_retirada = retirada_em or timezone.now()
            emprestimo = Emprestimo.objects.create(
                solicitante=solicitante,
                responsavel=responsavel,
                origem_conta_coletiva=origem_conta_coletiva,
                retirada_em=momento_retirada,
                observacao=observacao,
            )
            for recurso in recursos:
                ItemEmprestimo.objects.create(emprestimo=emprestimo, recurso=recurso)
            return emprestimo
        except IntegrityError:
            raise BusinessRuleException('O recurso já possui empréstimo em aberto.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível realizar o empréstimo.', logger)

    def realizar_emprestimo(
        self,
        solicitante_id: int,
        conta_autenticada,
        recurso_ids: list,
        observacao: str = '',
        retirada_em=None,
        responsavel_id=None,
        responsavel=None,
    ):
        try:
            self.object_instance.rules.pode_operar(conta_autenticada)
            if responsavel is None:
                responsavel = self.object_instance.rules.resolver_responsavel(
                    conta_autenticada, responsavel_id=responsavel_id
                )
            origem_conta_coletiva = self.object_instance.rules.resolver_origem_conta_coletiva(conta_autenticada)
            return self.criar_emprestimo_validado(
                solicitante_id=solicitante_id,
                responsavel=responsavel,
                recurso_ids=recurso_ids,
                observacao=observacao,
                retirada_em=retirada_em,
                origem_conta_coletiva=origem_conta_coletiva,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível realizar o empréstimo.', logger)

    def devolver_itens(self, conta_autenticada, item_ids: list):
        try:
            self.object_instance.rules.pode_operar(conta_autenticada)
            permitido = self.object_instance.helper.usuario_pode_consultar_emprestimo(
                conta_autenticada, self.object_instance
            )
            self.object_instance.rules.validar_consulta(permitido)
            self.object_instance.rules.pode_devolver_itens()
            itens = list(
                self.object_instance.itens.select_for_update().filter(pk__in=item_ids).select_related('recurso')
            )
            self.object_instance.rules.validar_itens_para_devolucao(itens, item_ids)
            agora = timezone.now()
            for item in itens:
                item.devolvido_em = agora
                item.save(update_fields=['devolvido_em'])
            return self.object_instance
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível devolver os itens do empréstimo.', logger)

    def transferir_titular_autorizado(
        self, novo_solicitante, responsavel, observacao: str = '', origem_conta_coletiva=None
    ):
        """Executa a troca após o fluxo chamador validar sua própria autorização."""
        try:
            from .models import Emprestimo

            emprestimo = Emprestimo.objects.select_for_update().get(pk=self.object_instance.pk)
            emprestimo.rules.pode_trocar_titular()
            itens_abertos = list(
                emprestimo.itens.select_for_update(of=('self',))
                .filter(devolvido_em__isnull=True)
                .select_related('recurso')
            )
            recurso_ids = [item.recurso_id for item in itens_abertos]
            agora = timezone.now()
            for item in itens_abertos:
                item.devolvido_em = agora
                item.save(update_fields=['devolvido_em'])
            return Emprestimo().business.criar_emprestimo_validado(
                solicitante_id=novo_solicitante.pk,
                responsavel=responsavel,
                recurso_ids=recurso_ids,
                observacao=observacao,
                retirada_em=agora,
                origem_conta_coletiva=origem_conta_coletiva,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível trocar o titular do empréstimo.', logger)

    def trocar_titular(self, conta_autenticada, novo_solicitante_id: int, observacao: str = '', responsavel_id=None):
        try:
            from .models import Emprestimo

            Usuario = apps.get_model(settings.AUTH_USER_MODEL)
            emprestimo = Emprestimo.objects.select_for_update().get(pk=self.object_instance.pk)
            emprestimo.rules.pode_operar(conta_autenticada)
            permitido = emprestimo.helper.usuario_pode_consultar_emprestimo(conta_autenticada, emprestimo)
            emprestimo.rules.validar_consulta(permitido)
            responsavel = emprestimo.rules.resolver_responsavel(conta_autenticada, responsavel_id=responsavel_id)
            origem_conta_coletiva = emprestimo.rules.resolver_origem_conta_coletiva(conta_autenticada)
            emprestimo.rules.validar_solicitante_ativo(novo_solicitante_id)
            novo_solicitante = Usuario.objects.get(pk=novo_solicitante_id)
            return emprestimo.business.transferir_titular_autorizado(
                novo_solicitante=novo_solicitante,
                responsavel=responsavel,
                observacao=observacao,
                origem_conta_coletiva=origem_conta_coletiva,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível trocar o titular do empréstimo.', logger)


class SolicitacaoTrocaTitularBusiness(ModelInstanceBusiness):

    def criar_solicitacao(self, emprestimo_id: int, solicitante, destinatario_id: int, observacao: str = ''):
        try:
            from .models import Emprestimo, SolicitacaoTrocaTitular

            Usuario = apps.get_model(settings.AUTH_USER_MODEL)
            Servidor = apps.get_model('servidores', 'Servidor')
            emprestimo = Emprestimo.objects.select_for_update().get(pk=emprestimo_id)
            destinatario = Usuario.objects.filter(pk=destinatario_id).first()
            itens_abertos = list(
                emprestimo.itens.select_for_update(of=('self',))
                .filter(devolvido_em__isnull=True)
                .select_related('recurso', 'recurso__sala', 'recurso__sala__bloco')
            )
            possui_pendente = SolicitacaoTrocaTitular.objects.filter(
                emprestimo=emprestimo, status=StatusSolicitacaoTrocaTitular.PENDENTE
            ).exists()
            self.object_instance.rules.validar_solicitante(solicitante, emprestimo)
            self.object_instance.rules.validar_emprestimo_aberto(bool(itens_abertos))
            self.object_instance.rules.validar_sem_solicitacao_pendente(possui_pendente)
            servidor_ativo = bool(
                destinatario and Servidor.objects.filter(usuario=destinatario, ativo=True).exists()
            )
            self.object_instance.rules.validar_destinatario(destinatario, servidor_ativo)
            self.object_instance.rules.validar_destinatario_diferente(destinatario.pk, emprestimo.solicitante_id)
            for item in itens_abertos:
                elegivel = emprestimo.helper.solicitante_pode_retirar_recurso(destinatario, item.recurso)
                self.object_instance.rules.validar_elegibilidade_destinatario(elegivel, item.recurso.codigo)
            return SolicitacaoTrocaTitular.objects.create(
                emprestimo=emprestimo, solicitante=solicitante, destinatario=destinatario, observacao=observacao
            )
        except IntegrityError:
            raise BusinessRuleException('Já existe uma solicitação de troca pendente para o empréstimo.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a solicitação.', logger)

    def listar_para_usuario(self, usuario, **filtros):
        try:
            return self.object_instance.helper.listar_para_usuario(usuario, **filtros)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar as solicitações.', logger)

    def obter_detalhada(self, solicitacao_id: int):
        try:
            return self.object_instance.helper.obter_detalhada(solicitacao_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível consultar a solicitação.', logger)

    def aceitar(self, solicitacao_id: int, usuario):
        try:
            from .models import Emprestimo, SolicitacaoTrocaTitular

            Servidor = apps.get_model('servidores', 'Servidor')
            solicitacao = (
                SolicitacaoTrocaTitular.objects.select_for_update()
                .select_related('destinatario')
                .get(pk=solicitacao_id)
            )
            solicitacao.rules.pode_aceitar(usuario)
            solicitacao.rules.validar_pendente()
            emprestimo = Emprestimo.objects.select_for_update().get(pk=solicitacao.emprestimo_id)
            itens_abertos = list(
                emprestimo.itens.select_for_update(of=('self',))
                .filter(devolvido_em__isnull=True)
                .select_related('recurso', 'recurso__sala', 'recurso__sala__bloco')
            )
            solicitacao.rules.validar_emprestimo_aberto(bool(itens_abertos))
            servidor_ativo = Servidor.objects.filter(usuario=solicitacao.destinatario, ativo=True).exists()
            solicitacao.rules.validar_destinatario(solicitacao.destinatario, servidor_ativo)
            for item in itens_abertos:
                elegivel = emprestimo.helper.solicitante_pode_retirar_recurso(
                    solicitacao.destinatario, item.recurso
                )
                solicitacao.rules.validar_elegibilidade_destinatario(elegivel, item.recurso.codigo)
            novo_emprestimo = emprestimo.business.transferir_titular_autorizado(
                novo_solicitante=solicitacao.destinatario,
                responsavel=solicitacao.destinatario,
                observacao=solicitacao.observacao,
            )
            solicitacao.novo_emprestimo = novo_emprestimo
            solicitacao.respondido_em = timezone.now()
            solicitacao.set_state(StatusSolicitacaoTrocaTitular.ACEITA)
            return solicitacao, novo_emprestimo
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível aceitar a solicitação.', logger)

    def recusar(self, solicitacao_id: int, usuario):
        try:
            from .models import SolicitacaoTrocaTitular

            solicitacao = SolicitacaoTrocaTitular.objects.select_for_update().get(pk=solicitacao_id)
            solicitacao.rules.pode_recusar(usuario)
            solicitacao.rules.validar_pendente()
            solicitacao.respondido_em = timezone.now()
            solicitacao.set_state(StatusSolicitacaoTrocaTitular.RECUSADA)
            return solicitacao
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível recusar a solicitação.', logger)

    def cancelar(self, solicitacao_id: int, usuario):
        try:
            from .models import SolicitacaoTrocaTitular

            solicitacao = SolicitacaoTrocaTitular.objects.select_for_update().get(pk=solicitacao_id)
            solicitacao.rules.pode_cancelar(usuario)
            solicitacao.rules.validar_pendente()
            solicitacao.respondido_em = timezone.now()
            solicitacao.set_state(StatusSolicitacaoTrocaTitular.CANCELADA)
            return solicitacao
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível cancelar a solicitação.', logger)
