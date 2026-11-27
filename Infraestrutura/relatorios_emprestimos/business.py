import logging
from datetime import date, timedelta

from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness

from Infraestrutura.emprestimos.choices import HORAS_ALERTA_ATRASO
from Infraestrutura.emprestimos.helpers import FUSO_HORARIO_EMPRESTIMOS
from Infraestrutura.permissoes.access import usuario_tem_acesso_total_infraestrutura
from .constantes import ROTULO_TIPO
from .dados import (
    DadosRelatorioEmprestimos,
    EmprestimoRelatorio,
    FiltroAplicado,
    ItemRelatorio,
    ResumoRelatorio,
)
from .pdf import renderizar_relatorio_emprestimos

logger = logging.getLogger(__name__)


class RelatorioEmprestimosBusiness(ModelInstanceBusiness):

    def gerar_pdf(self, usuario, filtros: dict) -> tuple[bytes, str]:
        try:
            data_inicio: date = filtros['data_inicio']
            data_fim: date = filtros['data_fim']
            self.object_instance.rules.validar_periodo(data_inicio, data_fim)

            bloco_id = filtros.get('bloco_id')
            sala_id = filtros.get('sala_id')
            if bloco_id and sala_id:
                pertence = self.object_instance.helper.sala_pertence_ao_bloco(sala_id, bloco_id)
                self.object_instance.rules.validar_sala_no_bloco(pertence)

            qs = self.object_instance.helper.listar_emprestimos(usuario, filtros)
            total = qs.count()
            self.object_instance.rules.validar_quantidade(total)

            dados = self._montar_dados_relatorio(usuario, filtros, qs)
            conteudo = renderizar_relatorio_emprestimos(dados)
            nome_arquivo = (
                f'relatorio-emprestimos_{data_inicio.isoformat()}_a_{data_fim.isoformat()}.pdf'
            )
            return conteudo, nome_arquivo
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível gerar o relatório de empréstimos em PDF.',
                logger,
            )

    def listar_pessoas(self, usuario, filtros: dict):
        try:
            return self.object_instance.helper.listar_pessoas(usuario, filtros)
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível listar pessoas para o relatório de empréstimos.',
                logger,
            )

    def _montar_dados_relatorio(self, usuario, filtros: dict, qs) -> DadosRelatorioEmprestimos:
        helper = self.object_instance.helper
        agora = timezone.now()
        limite_atraso = agora - timedelta(hours=HORAS_ALERTA_ATRASO)

        emprestimos_relatorio: list[EmprestimoRelatorio] = []
        total_itens = 0
        total_devolvidos = 0
        total_abertos = 0
        total_atrasados = 0

        for emprestimo in qs:
            itens_rel: list[ItemRelatorio] = []
            for item in emprestimo.itens.all():
                recurso = item.recurso
                situacao = self._situacao_item(item, emprestimo, limite_atraso)
                bloco_nome = ''
                sala_nome = ''
                if recurso.sala_id:
                    if recurso.sala and recurso.sala.bloco_id:
                        bloco_nome = recurso.sala.bloco.nome
                    sala_nome = recurso.sala.nome if recurso.sala else ''
                tipo_rotulo = ROTULO_TIPO.get(recurso.tipo, recurso.tipo)
                itens_rel.append(
                    ItemRelatorio(
                        codigo=recurso.codigo,
                        descricao=recurso.descricao or '',
                        tipo_rotulo=tipo_rotulo,
                        bloco=bloco_nome,
                        sala=sala_nome,
                        devolvido_em=item.devolvido_em,
                        situacao=situacao,
                    ),
                )
                total_itens += 1
                if situacao == 'Devolvido':
                    total_devolvidos += 1
                elif situacao == 'Em aberto':
                    total_abertos += 1
                elif situacao == 'Atrasado':
                    total_abertos += 1
                    total_atrasados += 1

            emprestimos_relatorio.append(
                EmprestimoRelatorio(
                    numero=emprestimo.pk,
                    retirada_em=emprestimo.retirada_em,
                    solicitante=emprestimo.solicitante.nome,
                    responsavel=emprestimo.responsavel.nome,
                    itens=itens_rel,
                ),
            )

        resumo = ResumoRelatorio(
            emprestimos=len(emprestimos_relatorio),
            itens=total_itens,
            devolvidos=total_devolvidos,
            em_aberto=total_abertos,
            atrasados=total_atrasados,
        )

        emitido_local = timezone.localtime(timezone.now(), FUSO_HORARIO_EMPRESTIMOS)
        emitido_rotulo = emitido_local.strftime('%d/%m/%Y %H:%M')

        return DadosRelatorioEmprestimos(
            periodo_inicio=filtros['data_inicio'],
            periodo_fim=filtros['data_fim'],
            emitido_em_rotulo=emitido_rotulo,
            emitido_por=usuario.nome,
            escopo=self._rotulo_escopo(usuario),
            filtros=self._montar_filtros_aplicados(helper, filtros),
            resumo=resumo,
            emprestimos=emprestimos_relatorio,
        )

    def _situacao_item(self, item, emprestimo, limite_atraso) -> str:
        if item.devolvido_em is not None:
            return 'Devolvido'
        if emprestimo.retirada_em < limite_atraso:
            return 'Atrasado'
        return 'Em aberto'

    def _rotulo_escopo(self, usuario) -> str:
        if usuario_tem_acesso_total_infraestrutura(usuario):
            return 'Todas as origens'
        if usuario.usuario_coletivo:
            return usuario.get_tipo_conta_coletiva_display()
        return 'Conta pessoal'

    def _montar_filtros_aplicados(self, helper, filtros: dict) -> list[FiltroAplicado]:
        solicitante_id = filtros.get('solicitante_id')
        responsavel_id = filtros.get('responsavel_id')
        tipo_recurso = filtros.get('tipo_recurso')
        bloco_id = filtros.get('bloco_id')
        sala_id = filtros.get('sala_id')

        rotulo_solicitante = helper.resolver_rotulo_pessoa(solicitante_id) if solicitante_id else None
        rotulo_responsavel = helper.resolver_rotulo_pessoa(responsavel_id) if responsavel_id else None
        rotulo_tipo = ROTULO_TIPO.get(tipo_recurso) if tipo_recurso else None
        rotulo_bloco = helper.resolver_rotulo_bloco(bloco_id) if bloco_id else None
        rotulo_sala = helper.resolver_rotulo_sala(sala_id) if sala_id else None

        return [
            FiltroAplicado('Solicitante', rotulo_solicitante or 'Todos'),
            FiltroAplicado('Entregue por', rotulo_responsavel or 'Todos'),
            FiltroAplicado(
                'Tipo de recurso',
                rotulo_tipo or 'Todos',
            ),
            FiltroAplicado('Bloco', rotulo_bloco or 'Todos'),
            FiltroAplicado('Sala', rotulo_sala or 'Todas'),
        ]