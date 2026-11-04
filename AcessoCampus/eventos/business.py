import logging
import uuid

from django.db.models import BooleanField, Case, F, Q, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException
from AcessoCampus.registros.choices import ResultadoRegistroAcesso
from AcessoCampus.solicitacoes.choices import HORA_AUTORIZADA_PADRAO
from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS, NOME_TIPO_SAIDA_CAMPUS

from .choices import StatusEventoAcesso

logger = logging.getLogger(__name__)


class EventoAcessoBusiness(ModelInstanceBusiness):

    def materializar_para_solicitacao(self, solicitacao, grupo_portaria_id=None):
        try:
            from .models import EventoAcesso

            evento, _ = EventoAcesso.objects.get_or_create(
                solicitacao=solicitacao,
                defaults={
                    'aluno_id': solicitacao.aluno_id,
                    'grupo_portaria_id': grupo_portaria_id or uuid.uuid4(),
                    'tipo_id': solicitacao.tipo_id,
                    'data_acesso': solicitacao.data_acesso,
                    'hora_prevista': solicitacao.hora_autorizada or HORA_AUTORIZADA_PADRAO,
                    'turma_origem': solicitacao.turma_origem,
                    'aluno_nome': solicitacao.aluno_nome,
                    'curso_nome': solicitacao.curso_nome,
                    'matricula': solicitacao.matricula,
                },
            )
            return evento
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o evento de acesso.', logger)

    def listar_grupos(self, filtros=None):
        try:
            filtros = filtros or {}
            qs = self.object_instance.helper.listar_representantes().annotate(
                total_registrados_normalizado=Coalesce('total_registrados', Value(0)),
                total_expirados_normalizado=Coalesce('total_expirados', Value(0)),
                status_operacional=Case(
                    When(total_registrados_normalizado=F('total_eventos'), then=Value(StatusEventoAcesso.CONCLUIDA)),
                    When(Q(total_expirados_normalizado__gt=0), then=Value(StatusEventoAcesso.EXPIRADA)),
                    default=Value(StatusEventoAcesso.PENDENTE),
                ),
            )
            if hasattr(filtros, 'getlist'):
                statuses_informados = filtros.getlist('status')
            else:
                status_informado = filtros.get('status')
                statuses_informados = (
                    status_informado if isinstance(status_informado, (list, tuple)) else [status_informado]
                )
            statuses = [status for status in statuses_informados if status in StatusEventoAcesso.values]
            if statuses:
                qs = qs.filter(status_operacional__in=statuses)
            busca = filtros.get('busca')
            if busca:
                qs = qs.filter(
                    Q(aluno_nome__unaccent__icontains=busca)
                    | Q(turma_origem__unaccent__icontains=busca)
                    | Q(solicitacao__avaliada_por__nome__unaccent__icontains=busca)
                )
            tipo_movimento = filtros.get('tipo_movimento')
            if tipo_movimento in ('ENTRADA', 'SAIDA'):
                nome_tipo = NOME_TIPO_ENTRADA_CAMPUS if tipo_movimento == 'ENTRADA' else NOME_TIPO_SAIDA_CAMPUS
                qs = qs.filter(tipo__nome=nome_tipo)
            tipo_beneficiario = filtros.get('tipo_beneficiario')
            if tipo_beneficiario == 'TURMA':
                qs = qs.exclude(turma_origem='')
            elif tipo_beneficiario == 'INDIVIDUAL':
                qs = qs.filter(turma_origem='')
            data_autorizada = parse_date(filtros.get('data_autorizada') or '')
            if data_autorizada:
                qs = qs.filter(data_acesso=data_autorizada)
            hora_inicio = parse_time(filtros.get('hora_inicio') or '')
            if hora_inicio:
                qs = qs.filter(hora_prevista__gte=hora_inicio)
            hora_fim = parse_time(filtros.get('hora_fim') or '')
            if hora_fim:
                qs = qs.filter(hora_prevista__lte=hora_fim)
            ordenacoes = {
                'nome': 'aluno_nome',
                '-nome': '-aluno_nome',
                'tipo_movimento': 'tipo__nome',
                '-tipo_movimento': '-tipo__nome',
                'autorizado_por': 'solicitacao__avaliada_por__nome',
                '-autorizado_por': '-solicitacao__avaliada_por__nome',
                'data_autorizada': 'data_acesso',
                '-data_autorizada': '-data_acesso',
                'hora_autorizada': 'hora_prevista',
                '-hora_autorizada': '-hora_prevista',
            }
            ordenacao_param = filtros.get('ordenacao')
            status_encerrados = {StatusEventoAcesso.CONCLUIDA, StatusEventoAcesso.EXPIRADA}
            if not ordenacao_param and statuses and set(statuses).issubset(status_encerrados):
                return qs.order_by(
                    '-data_acesso',
                    '-hora_prevista',
                    'grupo_portaria_id',
                )
            ordenacao = ordenacoes.get(ordenacao_param, 'data_acesso')
            return qs.order_by(ordenacao, 'hora_prevista', 'grupo_portaria_id')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar as autorizações.', logger)

    def obter_grupo(self, grupo_portaria_id, bloquear=False):
        try:
            eventos = list(self.object_instance.helper.eventos_do_grupo(grupo_portaria_id, bloquear))
            if not eventos:
                raise NotFoundException('Autorização de acesso não encontrada.')
            for evento in eventos:
                evento._eventos_serializacao = eventos
            return eventos
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter a autorização.', logger)

    def listar_alunos_grupo(self, grupo_portaria_id, filtros=None):
        try:
            filtros = filtros or {}
            qs = self.object_instance.helper.eventos_do_grupo(grupo_portaria_id)
            if not qs.exists():
                raise NotFoundException('Autorização de acesso não encontrada.')
            busca = filtros.get('busca')
            if busca:
                qs = qs.filter(Q(aluno_nome__unaccent__icontains=busca) | Q(aluno__usuario__cpf__icontains=busca))
            agora = timezone.localtime()
            disponivel = Q(registro__isnull=True, expirado_em__isnull=True) & (
                Q(data_acesso__gt=agora.date())
                | Q(data_acesso=agora.date(), hora_prevista__gte=agora.time().replace(tzinfo=None))
            )
            return qs.annotate(
                pode_liberar_operacional=Case(
                    When(disponivel, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            ).order_by(F('registro__registrado_em').desc(nulls_last=True), 'aluno_nome')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os alunos da autorização.', logger)

    def listar_responsaveis(self, operador, filtros=None):
        try:
            from Identidade.usuarios.models import Usuario

            filtros = filtros or {}
            if operador.is_staff or operador.is_admin or operador.is_superuser:
                return Usuario.objects.filter(pk=operador.pk, ativo=True)
            return Usuario().helper.listar_responsaveis_do_coletivo(
                operador, nome=filtros.get('busca'), cpf=filtros.get('cpf')
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os responsáveis.', logger)

    def registrar(self, grupo_portaria_id, operador, responsavel_id=None, aluno_ids=None, observacao=''):
        try:
            from AcessoCampus.registros.models import RegistroAcesso

            eventos = self.obter_grupo(grupo_portaria_id, bloquear=True)
            self.object_instance.rules.validar_grupo_pendente(eventos)
            self.object_instance.rules.validar_identificacao_responsavel(operador, responsavel_id)
            responsavel = operador
            operador_tem_acesso_total = operador.is_staff or operador.is_admin or operador.is_superuser
            if operador.usuario_coletivo and not operador_tem_acesso_total:
                from Identidade.usuarios.models import Usuario

                responsavel = (
                    Usuario().helper.listar_responsaveis_do_coletivo(operador).filter(pk=responsavel_id).first()
                )
                self.object_instance.rules.validar_responsavel_elegivel(responsavel)
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
                        'resultado': ResultadoRegistroAcesso.REALIZADO,
                        'registrado_por': responsavel,
                        'operado_por': operador,
                        'observacao': observacao or '',
                    },
                )
                criados += int(criado)
                repetidos += int(not criado)
            atualizados = self.obter_grupo(grupo_portaria_id)
            return atualizados, {'solicitados': len(alvos), 'confirmados_agora': criados, 'ja_confirmados': repetidos}
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível registrar o acesso.', logger)

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
            self.relancar_ou_erro_sistema(e, 'Não foi possível expirar os eventos de acesso.', logger)
