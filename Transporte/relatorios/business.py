import logging
from datetime import date

from django.core.paginator import Paginator

from AppCore.core.exceptions.exceptions import ValidationException

from .choices import CategoriaRelatorioAluno
from .helpers import RelatorioAlunosHelpers
from .rules import RelatorioAlunosRules
from Transporte.tickets.choices import StatusTicket

logger = logging.getLogger(__name__)


class RelatorioAlunosBusiness:

    def __init__(self):
        self.helper = RelatorioAlunosHelpers()
        self.rules = RelatorioAlunosRules()

    def obter_dashboard(self, data_inicio: date, data_fim: date):
        try:
            self.rules.validar_periodo(data_inicio, data_fim)
            tickets = self.helper.obter_tickets_no_periodo(data_inicio, data_fim)
            bloqueados_ids = self.helper.obter_ids_alunos_bloqueados()

            alunos_bloqueados_no_periodo = tickets.filter(
                aluno_id__in=bloqueados_ids,
            ).values('aluno_id').distinct().count()

            sem_ticket = self.helper.obter_alunos_sem_ticket_no_periodo(
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

            por_horario = self.helper.montar_resumo_por_horario(
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
        except (ValidationException,):
            raise
        except Exception as e:
            from AppCore.core.business.business import ModelInstanceBusiness

            business = ModelInstanceBusiness()
            business.relancar_ou_erro_sistema(
                e,
                'Não foi possível gerar o dashboard do relatório de alunos.',
                logger,
            )

    def obter_detalhes(
        self,
        data_inicio: date,
        data_fim: date,
        categoria: str,
        busca: str = '',
        page: int = 1,
        paginacao: int = 10,
    ):
        try:
            self.rules.validar_periodo(data_inicio, data_fim)
            self.rules.validar_categoria(categoria)

            alunos = self._listar_alunos_por_categoria(data_inicio, data_fim, categoria)

            if busca.strip():
                termo = busca.strip()
                alunos = alunos.filter(usuario__nome__icontains=termo)

            alunos = alunos.select_related('usuario').order_by('usuario__nome')

            paginator = Paginator(alunos, paginacao)
            pagina = paginator.get_page(page)

            dados = [
                self.helper.enriquecer_aluno(aluno, data_inicio, data_fim, categoria)
                for aluno in pagina.object_list
            ]

            return {
                'categoria': categoria,
                'count': paginator.count,
                'next': page + 1 if pagina.has_next() else None,
                'previous': page - 1 if pagina.has_previous() else None,
                'results': dados,
            }
        except (ValidationException,):
            raise
        except Exception as e:
            from AppCore.core.business.business import ModelInstanceBusiness

            business = ModelInstanceBusiness()
            business.relancar_ou_erro_sistema(
                e,
                'Não foi possível gerar os detalhes do relatório de alunos.',
                logger,
            )

    def _listar_alunos_por_categoria(self, data_inicio: date, data_fim: date, categoria: str):
        from Academico.alunos.models import Aluno

        tickets = self.helper.obter_tickets_no_periodo(data_inicio, data_fim)
        bloqueados_ids = self.helper.obter_ids_alunos_bloqueados()

        if categoria == CategoriaRelatorioAluno.PRESENTES:
            ids = tickets.filter(status=StatusTicket.EMBARCADO).values_list('aluno_id', flat=True)
            return Aluno.objects.filter(usuario_id__in=ids)

        if categoria == CategoriaRelatorioAluno.AUSENCIAS:
            ids = tickets.filter(status=StatusTicket.AUSENTE).values_list('aluno_id', flat=True)
            return Aluno.objects.filter(usuario_id__in=ids)

        if categoria == CategoriaRelatorioAluno.BLOQUEIOS:
            ids = tickets.filter(aluno_id__in=bloqueados_ids).values_list('aluno_id', flat=True)
            return Aluno.objects.filter(usuario_id__in=ids).distinct()

        return self.helper.obter_alunos_sem_ticket_no_periodo(data_inicio, data_fim)
