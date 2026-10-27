import logging
import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import AuthorizationException, BusinessRuleException

from .choices import (
    HORA_AUTORIZADA_PADRAO,
    OrigemSolicitacaoAcesso,
    StatusSolicitacaoAcesso,
)
from .escopo import usuario_tem_escopo_global, vinculos_no_escopo
from .rules import MENSAGEM_AUTORIZACAO_JA_ACEITA

logger = logging.getLogger(__name__)

NOME_CONSTRAINT_ACEITA = 'uniq_acesso_aceito_aluno_data_tipo'


def _eh_autorizacao_duplicada(exc) -> bool:
    texto = str(exc)
    if NOME_CONSTRAINT_ACEITA in texto:
        return True
    return 'UNIQUE constraint failed' in texto and 'aluno_id' in texto and 'data_acesso' in texto


class SolicitacaoAcessoBusiness(ModelInstanceBusiness):

    def autorizar(
        self,
        usuario,
        tipo,
        data_acesso,
        hora_autorizada,
        motivo,
        observacao='',
        aluno_curso_ids=None,
        curso_id=None,
        turma=None,
    ):
        try:
            from .models import SolicitacaoAcesso

            self._validar_escopo_de_escrita(usuario)
            self.object_instance.rules.validar_alvo_autorizacao(aluno_curso_ids, curso_id, turma)
            self.object_instance.rules.validar_data_nao_passada(data_acesso)
            vinculos = self._vinculos_para_autorizar(usuario, aluno_curso_ids, curso_id, turma)
            agora = timezone.now()
            lote_id = uuid.uuid4()
            turma_origem = turma or ''
            criadas = []
            with transaction.atomic():
                aluno_ids = [vinculo.aluno_id for vinculo in vinculos]
                ja_existe = self.object_instance.helper.existe_autorizacao_aceita(
                    aluno_ids,
                    data_acesso,
                    tipo,
                )
                self.object_instance.rules.validar_autorizacao_aceita_unica(aluno_ids, ja_existe)
                for vinculo in vinculos:
                    criadas.append(
                        SolicitacaoAcesso.objects.create(
                            aluno_id=vinculo.aluno_id,
                            aluno_curso=vinculo,
                            origem=OrigemSolicitacaoAcesso.GESTAO,
                            tipo=tipo,
                            status=StatusSolicitacaoAcesso.ACEITA,
                            data_acesso=data_acesso,
                            hora_solicitada=None,
                            hora_autorizada=hora_autorizada,
                            motivo=motivo,
                            justificativa='',
                            observacao_avaliacao=observacao or '',
                            avaliada_por=usuario,
                            avaliada_em=agora,
                            lote_id=lote_id,
                            turma_origem=turma_origem,
                            aluno_nome=vinculo.aluno.usuario.nome,
                            curso_nome=vinculo.curso.nome,
                            matricula=vinculo.matricula or '',
                        )
                    )
            return criadas
        except IntegrityError as exc:
            if _eh_autorizacao_duplicada(exc):
                raise BusinessRuleException(MENSAGEM_AUTORIZACAO_JA_ACEITA)
            self.relancar_ou_erro_sistema(exc, 'Não foi possível autorizar o acesso.', logger)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível autorizar o acesso.', logger)

    def aceitar(self, usuario, hora_autorizada=None, observacao=''):
        try:
            from .models import SolicitacaoAcesso

            with transaction.atomic():
                solicitacao = SolicitacaoAcesso.objects.select_for_update().get(
                    pk=self.object_instance.pk,
                )
                solicitacao.rules.validar_status_pendente()
                solicitacao.rules.validar_data_nao_passada(solicitacao.data_acesso)
                ja_existe = solicitacao.helper.existe_autorizacao_aceita(
                    [solicitacao.aluno_id],
                    solicitacao.data_acesso,
                    solicitacao.tipo,
                    excluir_pk=solicitacao.pk,
                )
                solicitacao.rules.validar_autorizacao_aceita_unica(
                    [solicitacao.aluno_id],
                    ja_existe,
                )
                solicitacao.status = StatusSolicitacaoAcesso.ACEITA
                solicitacao.hora_autorizada = hora_autorizada or HORA_AUTORIZADA_PADRAO
                solicitacao.observacao_avaliacao = observacao or ''
                solicitacao.avaliada_por = usuario
                solicitacao.avaliada_em = timezone.now()
                solicitacao.save()
            self.object_instance = solicitacao
            return solicitacao
        except IntegrityError as exc:
            if _eh_autorizacao_duplicada(exc):
                raise BusinessRuleException(MENSAGEM_AUTORIZACAO_JA_ACEITA)
            self.relancar_ou_erro_sistema(exc, 'Não foi possível aceitar a solicitação.', logger)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível aceitar a solicitação.', logger)

    def recusar(self, usuario, observacao=''):
        try:
            from .models import SolicitacaoAcesso

            with transaction.atomic():
                solicitacao = SolicitacaoAcesso.objects.select_for_update().get(
                    pk=self.object_instance.pk,
                )
                solicitacao.rules.validar_status_pendente()
                solicitacao.status = StatusSolicitacaoAcesso.RECUSADA
                solicitacao.observacao_avaliacao = observacao or ''
                solicitacao.avaliada_por = usuario
                solicitacao.avaliada_em = timezone.now()
                solicitacao.save()
            self.object_instance = solicitacao
            return solicitacao
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível recusar a solicitação.', logger)

    def _validar_escopo_de_escrita(self, usuario):
        from .escopo import curso_ids_sob_coordenacao

        if usuario_tem_escopo_global(usuario):
            return
        if not curso_ids_sob_coordenacao(usuario).exists():
            raise AuthorizationException('Você não tem cursos sob sua coordenação.')

    def _vinculos_para_autorizar(self, usuario, aluno_curso_ids, curso_id, turma):
        qs = vinculos_no_escopo(usuario).select_related('aluno__usuario', 'curso')
        if aluno_curso_ids:
            ids = list(dict.fromkeys(aluno_curso_ids))
            vinculos = list(qs.filter(pk__in=ids))
            self.object_instance.rules.validar_vinculos_encontrados(len(ids), len(vinculos))
            return vinculos
        vinculos = list(qs.filter(curso_id=curso_id, turma=turma))
        self.object_instance.rules.validar_turma_com_alunos(len(vinculos))
        return vinculos
