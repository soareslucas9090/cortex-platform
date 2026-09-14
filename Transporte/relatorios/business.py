import logging
from datetime import date

from django.core.paginator import Paginator

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import ValidationException

from Transporte.tickets.choices import StatusTicket

from .choices import CategoriaRelatorioAluno

logger = logging.getLogger(__name__)


class RelatorioAlunosBusiness(ModelInstanceBusiness):

    def obter_periodo(self, parametros):
        try:
            data_inicio_param = parametros.get('data_inicio')
            data_fim_param = parametros.get('data_fim')
            self.object_instance.rules.validar_parametro_obrigatorio(
                data_inicio_param,
                'data_inicio',
            )
            self.object_instance.rules.validar_parametro_obrigatorio(
                data_fim_param,
                'data_fim',
            )
            data_inicio = date.fromisoformat(data_inicio_param)
            data_fim = date.fromisoformat(data_fim_param)
            self.object_instance.rules.validar_periodo(data_inicio, data_fim)
            return data_inicio, data_fim
        except ValueError:
            raise ValidationException(
                'data_inicio e data_fim devem estar no formato AAAA-MM-DD.',
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível validar o período do relatório de alunos.',
                logger,
            )

    def obter_paginacao(self, parametros):
        try:
            try:
                page = int(parametros.get('page', 1))
            except (TypeError, ValueError):
                page = 1
            try:
                paginacao = int(parametros.get('paginacao', 10))
            except (TypeError, ValueError):
                paginacao = 10
            return max(page, 1), min(max(paginacao, 1), 100)
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível validar a paginação do relatório de alunos.',
                logger,
            )

    def obter_dashboard(self, parametros):
        try:
            data_inicio, data_fim = self.obter_periodo(parametros)
            helper = self.object_instance.helper
            tickets = helper.obter_tickets_no_periodo(data_inicio, data_fim)
            bloqueados_ids = helper.obter_ids_alunos_bloqueados()

            alunos_bloqueados_no_periodo = tickets.filter(
                aluno_id__in=bloqueados_ids,
            ).values('aluno_id').distinct().count()

            sem_ticket = helper.obter_entradas_sem_ticket_no_periodo(
                data_inicio,
                data_fim,
            ).count()

            resumo = {
                'presentes': tickets.filter(status=StatusTicket.EMBARCADO).count(),
                'ausentes': tickets.filter(status=StatusTicket.AUSENTE).count(),
                'em_espera': tickets.filter(status=StatusTicket.EM_ESPERA).count(),
                'bloqueados': alunos_bloqueados_no_periodo,
                'sem_ticket': sem_ticket,
            }

            por_horario = helper.montar_resumo_por_horario(
                tickets,
                bloqueados_ids,
                data_inicio,
                data_fim,
            )

            return {
                'periodo': {
                    'data_inicio': data_inicio,
                    'data_fim': data_fim,
                },
                'resumo': resumo,
                'por_horario': por_horario,
            }
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível gerar o dashboard do relatório de alunos.',
                logger,
            )

    def obter_detalhes(self, parametros):
        try:
            data_inicio, data_fim = self.obter_periodo(parametros)
            categoria = parametros.get('categoria')
            self.object_instance.rules.validar_parametro_obrigatorio(
                categoria,
                'categoria',
            )
            self.object_instance.rules.validar_categoria(categoria)
            page, paginacao = self.obter_paginacao(parametros)
            busca = parametros.get('busca', '') or ''

            alunos = self._listar_alunos_por_categoria(data_inicio, data_fim, categoria)

            if busca.strip():
                termo = busca.strip()
                alunos = alunos.filter(usuario__nome__icontains=termo)

            alunos = alunos.select_related('usuario').order_by('usuario__nome')

            paginator = Paginator(alunos, paginacao)
            pagina = paginator.get_page(page)

            dados = [
                self.object_instance.helper.enriquecer_aluno(
                    aluno,
                    data_inicio,
                    data_fim,
                    categoria,
                )
                for aluno in pagina.object_list
            ]

            return {
                'categoria': categoria,
                'count': paginator.count,
                'next': pagina.next_page_number() if pagina.has_next() else None,
                'previous': (
                    pagina.previous_page_number() if pagina.has_previous() else None
                ),
                'results': dados,
            }
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível gerar os detalhes do relatório de alunos.',
                logger,
            )

    def _listar_alunos_por_categoria(
        self,
        data_inicio: date,
        data_fim: date,
        categoria: str,
    ):
        from Academico.alunos.models import Aluno

        try:
            helper = self.object_instance.helper
            tickets = helper.obter_tickets_no_periodo(data_inicio, data_fim)
            bloqueados_ids = helper.obter_ids_alunos_bloqueados()

            if categoria == CategoriaRelatorioAluno.PRESENTES:
                ids = tickets.filter(status=StatusTicket.EMBARCADO).values_list(
                    'aluno_id',
                    flat=True,
                )
                return Aluno.objects.filter(usuario_id__in=ids)

            if categoria == CategoriaRelatorioAluno.AUSENCIAS:
                ids = tickets.filter(status=StatusTicket.AUSENTE).values_list(
                    'aluno_id',
                    flat=True,
                )
                return Aluno.objects.filter(usuario_id__in=ids)

            if categoria == CategoriaRelatorioAluno.BLOQUEIOS:
                ids = tickets.filter(aluno_id__in=bloqueados_ids).values_list(
                    'aluno_id',
                    flat=True,
                )
                return Aluno.objects.filter(usuario_id__in=ids).distinct()

            if categoria == CategoriaRelatorioAluno.SEM_TICKET:
                return helper.obter_alunos_sem_ticket_no_periodo(data_inicio, data_fim)

            return Aluno.objects.none()
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível listar os alunos do relatório.',
                logger,
            )
