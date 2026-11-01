import logging
import uuid

from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException
from AcessoCampus.registros.choices import ResultadoRegistroAcesso
from AcessoCampus.solicitacoes.choices import HORA_AUTORIZADA_PADRAO

from .choices import StatusEventoAcesso

logger = logging.getLogger(__name__)


class EventoAcessoBusiness(ModelInstanceBusiness):

    def materializar_para_solicitacao(self, solicitacao, grupo_portaria_id=None):
        try:
            from .models import EventoAcesso

            evento, _ = EventoAcesso.objects.get_or_create(
                solicitacao=solicitacao,
                defaults={
                    "aluno_id": solicitacao.aluno_id,
                    "grupo_portaria_id": grupo_portaria_id or uuid.uuid4(),
                    "tipo": solicitacao.tipo,
                    "data_acesso": solicitacao.data_acesso,
                    "hora_prevista": solicitacao.hora_autorizada or HORA_AUTORIZADA_PADRAO,
                    "turma_origem": solicitacao.turma_origem,
                    "aluno_nome": solicitacao.aluno_nome,
                    "curso_nome": solicitacao.curso_nome,
                    "matricula": solicitacao.matricula,
                },
            )
            return evento
        except Exception as e:
            self.relancar_ou_erro_sistema(e, "Não foi possível criar o evento de acesso.", logger)

    def listar_grupos(self, filtros=None):
        try:
            filtros = filtros or {}
            self.expirar_pendentes()
            qs = self.object_instance.helper.listar_representantes().annotate(
                total_registrados_normalizado=Coalesce("total_registrados", Value(0)),
                total_expirados_normalizado=Coalesce("total_expirados", Value(0)),
                status_operacional=Case(
                    When(total_registrados_normalizado=F("total_eventos"), then=Value(StatusEventoAcesso.CONCLUIDA)),
                    When(Q(total_expirados_normalizado__gt=0), then=Value(StatusEventoAcesso.EXPIRADA)),
                    default=Value(StatusEventoAcesso.PENDENTE),
                ),
            )
            statuses = filtros.getlist("status") if hasattr(filtros, "getlist") else []
            if statuses:
                qs = qs.filter(status_operacional__in=statuses)
            busca = filtros.get("busca")
            if busca:
                qs = qs.filter(
                    Q(aluno_nome__unaccent__icontains=busca)
                    | Q(turma_origem__unaccent__icontains=busca)
                    | Q(solicitacao__avaliada_por__nome__unaccent__icontains=busca)
                )
            tipo_movimento = filtros.get("tipo_movimento")
            if tipo_movimento in ("ENTRADA", "SAIDA"):
                qs = qs.filter(tipo=1 if tipo_movimento == "ENTRADA" else 2)
            tipo_beneficiario = filtros.get("tipo_beneficiario")
            if tipo_beneficiario == "TURMA":
                qs = qs.exclude(turma_origem="")
            elif tipo_beneficiario == "INDIVIDUAL":
                qs = qs.filter(turma_origem="")
            if filtros.get("data_autorizada"):
                qs = qs.filter(data_acesso=filtros["data_autorizada"])
            if filtros.get("hora_inicio"):
                qs = qs.filter(hora_prevista__gte=filtros["hora_inicio"])
            if filtros.get("hora_fim"):
                qs = qs.filter(hora_prevista__lte=filtros["hora_fim"])
            ordenacoes = {
                "nome": "aluno_nome",
                "-nome": "-aluno_nome",
                "tipo_movimento": "tipo",
                "-tipo_movimento": "-tipo",
                "autorizado_por": "solicitacao__avaliada_por__nome",
                "-autorizado_por": "-solicitacao__avaliada_por__nome",
                "data_autorizada": "data_acesso",
                "-data_autorizada": "-data_acesso",
                "hora_autorizada": "hora_prevista",
                "-hora_autorizada": "-hora_prevista",
            }
            ordenacao = ordenacoes.get(filtros.get("ordenacao"), "data_acesso")
            return qs.order_by(ordenacao, "hora_prevista", "grupo_portaria_id")
        except Exception as e:
            self.relancar_ou_erro_sistema(e, "Não foi possível listar as autorizações.", logger)

    def obter_grupo(self, grupo_portaria_id, bloquear=False):
        try:
            eventos = list(self.object_instance.helper.eventos_do_grupo(grupo_portaria_id, bloquear))
            if not eventos:
                raise NotFoundException("Autorização de acesso não encontrada.")
            return eventos
        except Exception as e:
            self.relancar_ou_erro_sistema(e, "Não foi possível obter a autorização.", logger)

    def listar_alunos_grupo(self, grupo_portaria_id, filtros=None):
        try:
            filtros = filtros or {}
            self.expirar_pendentes()
            qs = self.object_instance.helper.eventos_do_grupo(grupo_portaria_id)
            if not qs.exists():
                raise NotFoundException("Autorização de acesso não encontrada.")
            busca = filtros.get("busca")
            if busca:
                qs = qs.filter(Q(aluno_nome__unaccent__icontains=busca) | Q(aluno__usuario__cpf__icontains=busca))
            return qs.order_by(F("registro__registrado_em").desc(nulls_last=True), "aluno_nome")
        except Exception as e:
            self.relancar_ou_erro_sistema(e, "Não foi possível listar os alunos da autorização.", logger)

    def listar_responsaveis(self, operador, filtros=None):
        try:
            from Identidade.usuarios.models import Usuario

            filtros = filtros or {}
            if operador.is_staff or operador.is_admin or operador.is_superuser:
                return Usuario.objects.filter(pk=operador.pk, ativo=True)
            return Usuario().helper.listar_responsaveis_do_coletivo(
                operador, nome=filtros.get("busca"), cpf=filtros.get("cpf")
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, "Não foi possível listar os responsáveis.", logger)

    def registrar(self, grupo_portaria_id, operador, responsavel_id=None, aluno_ids=None, observacao=""):
        try:
            from AcessoCampus.registros.models import RegistroAcesso

            eventos = self.obter_grupo(grupo_portaria_id, bloquear=True)
            self.object_instance.rules.validar_grupo_pendente(eventos)
            responsavel = self.object_instance.rules.resolver_responsavel(operador, responsavel_id)
            eh_turma = bool(eventos[0].turma_origem)
            if eh_turma:
                self.object_instance.rules.validar_alunos_do_grupo(eventos, aluno_ids)
                ids_alvo = set(aluno_ids)
                alvos = [evento for evento in eventos if evento.aluno_id in ids_alvo]
            else:
                alvos = eventos
            criados = 0
            repetidos = 0
            for evento in alvos:
                _, criado = RegistroAcesso.objects.get_or_create(
                    evento=evento,
                    defaults={
                        "resultado": ResultadoRegistroAcesso.REALIZADO,
                        "registrado_por": responsavel,
                        "operado_por": operador,
                        "observacao": observacao or "",
                    },
                )
                criados += int(criado)
                repetidos += int(not criado)
            atualizados = self.obter_grupo(grupo_portaria_id)
            return atualizados, {"solicitados": len(alvos), "confirmados_agora": criados, "ja_confirmados": repetidos}
        except Exception as e:
            self.relancar_ou_erro_sistema(e, "Não foi possível registrar o acesso.", logger)

    def expirar_pendentes(self):
        try:
            from .models import EventoAcesso

            limite = timezone.localtime()
            hora_limite = limite.time().replace(tzinfo=None)
            return (
                EventoAcesso.objects.filter(expirado_em__isnull=True, registro__isnull=True)
                .filter(Q(data_acesso__lt=limite.date()) | Q(data_acesso=limite.date(), hora_prevista__lt=hora_limite))
                .update(expirado_em=timezone.now())
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, "Não foi possível expirar os eventos de acesso.", logger)
