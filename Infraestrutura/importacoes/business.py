import logging

from django.db import IntegrityError, transaction

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import (
    BusinessRuleException,
    NotFoundException,
    SystemErrorException,
    ValidationException,
)

from .importacao.importacao_constants import CODIGO_ERRO_FOTO
from .importacao.importacao_dtos import (
    ErroImportacaoDTO,
    ResumoImportacaoDTO,
    ResultadoImportacaoDTO,
)
from .importacao.importacao_parser import ImportacaoInfraestruturaParser
from .helpers import (
    baixar_imagem_de_url,
    obter_bloco_por_id_planilha,
    obter_sala_por_id_planilha,
)

logger = logging.getLogger(__name__)


class ImportacaoLoteBusiness(ModelInstanceBusiness):

    def obter_arquivo_modelo_importacao(self):
        """Obtém o stream e o content-type do modelo ODS de importação no S3."""
        try:
            from botocore.exceptions import ClientError

            from AppCore.common.storage.s3 import iterar_objeto_s3
            from .constantes import CHAVE_MODELO_IMPORTACAO_INFRAESTRUTURA

            return iterar_objeto_s3(
                CHAVE_MODELO_IMPORTACAO_INFRAESTRUTURA,
                content_type_padrao='application/vnd.oasis.opendocument.spreadsheet',
            )
        except ClientError:
            raise NotFoundException('Arquivo modelo de importação não encontrado no bucket.')
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível obter o arquivo modelo de importação.',
                logger,
            )

    def _validar_sem_importacao_em_andamento(self):
        from .models import ImportacaoLote, StatusImportacao

        if ImportacaoLote.objects.filter(status=StatusImportacao.EM_ANDAMENTO).exists():
            raise ValidationException(
                'Já existe uma importação em andamento. Aguarde o término.'
            )

    def iniciar_importacao(self, arquivo):
        """Cria lote, envia arquivo ao S3 e enfileira processamento assíncrono."""
        try:
            from .importacao.s3_helper import upload_importacao_to_s3
            from .models import ImportacaoLote
            from .tasks import processar_importacao_infraestrutura_task

            self._validar_sem_importacao_em_andamento()

            importacao = ImportacaoLote.objects.create(arquivo=arquivo)

            if not upload_importacao_to_s3(importacao):
                raise SystemErrorException('Não foi possível iniciar a importação.')

            transaction.on_commit(
                lambda: processar_importacao_infraestrutura_task.delay(importacao.id)
            )
            return importacao.id
        except IntegrityError:
            raise BusinessRuleException(
                'Já existe uma importação em andamento. Aguarde o término.'
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível iniciar a importação.', logger)

    def cancelar_importacoes_em_andamento(self):
        """Cancela importações com status EM_ANDAMENTO."""
        try:
            from .models import ImportacaoLote, StatusImportacao

            importacoes = list(
                ImportacaoLote.objects.filter(status=StatusImportacao.EM_ANDAMENTO)
            )
            if not importacoes:
                raise ValidationException(
                    'Não há nenhuma importação em andamento para ser cancelada.'
                )

            for importacao in importacoes:
                importacao.status = StatusImportacao.ERRO
                resultado = importacao.resultado_json or {}
                resultado['erro_fatal'] = (
                    'Importação cancelada manualmente pelo administrador.'
                )
                importacao.resultado_json = resultado
                importacao.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível cancelar a importação.', logger
            )

    def obter_status_recente(self):
        """Retorna a importação mais recente ou levanta NotFoundException."""
        try:
            from .models import ImportacaoLote

            ultima_importacao = ImportacaoLote.objects.order_by('-created_at').first()
            if not ultima_importacao:
                raise NotFoundException('Nenhuma importação encontrada.')
            return ultima_importacao
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível obter o status da importação.', logger
            )

    def pre_visualizar_importacao(self, arquivo):
        """Executa validação estrutural sem persistência nem download de fotos."""
        try:
            self._validar_sem_importacao_em_andamento()

            parser = ImportacaoInfraestruturaParser()
            estrutura = parser.parse(arquivo)
            resumo = ResumoImportacaoDTO()
            erros = []
            resumo.total_abas_processadas = self._contar_abas_processadas(estrutura)
            resumo.total_linhas_processadas = self._contar_linhas_processadas(estrutura)
            try:
                self._validar_estrutura_importacao(estrutura)
            except Exception as exc:
                erros.append(
                    ErroImportacaoDTO(
                        aba='__arquivo__',
                        numero_linha=0,
                        campo='arquivo',
                        valor=None,
                        codigo='estrutura_invalida',
                        mensagem=str(exc),
                    )
                )
            return ResultadoImportacaoDTO(
                sucesso=len(erros) == 0,
                mensagem=(
                    'Pré-visualização concluída.'
                    if not erros
                    else 'Pré-visualização concluída com pendências.'
                ),
                resumo=resumo,
                erros=erros,
                metadados={'modo': 'preview'},
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar pre_visualizar_importacao.', logger
            )

    def importar_infraestrutura_em_lote(self, importacao_lote):
        """Processa o arquivo ODS e persiste blocos, salas e recursos."""
        try:
            parser = ImportacaoInfraestruturaParser()
            estrutura = parser.parse(importacao_lote.arquivo)
            self._validar_estrutura_importacao(estrutura)
            resumo = ResumoImportacaoDTO()
            erros = []
            mapa_blocos = {}
            mapa_salas = {}
            resumo.total_abas_processadas = self._contar_abas_processadas(estrutura)
            resumo.total_linhas_processadas = self._contar_linhas_processadas(estrutura)
            importacao_lote.total_linhas = resumo.total_linhas_processadas
            importacao_lote.save(update_fields=['total_linhas'])

            def _incrementar_progresso():
                importacao_lote.linhas_processadas += 1
                from .models import ImportacaoLote, StatusImportacao

                status_atual = ImportacaoLote.objects.filter(
                    id=importacao_lote.id
                ).values_list('status', flat=True).first()
                if status_atual != StatusImportacao.EM_ANDAMENTO:
                    raise Exception(
                        'Importação cancelada manualmente pelo administrador.'
                    )
                if (
                    importacao_lote.linhas_processadas % 10 == 0
                    or importacao_lote.linhas_processadas == importacao_lote.total_linhas
                ):
                    importacao_lote.save(update_fields=['linhas_processadas'])

            for linha in estrutura.blocos:
                _incrementar_progresso()
                try:
                    with transaction.atomic():
                        bloco, criado = self._criar_ou_atualizar_bloco(linha)
                        mapa_blocos[linha.bloco_id_planilha] = bloco
                        if criado:
                            resumo.blocos_criados += 1
                        else:
                            resumo.blocos_atualizados += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            'bloco',
                            linha.numero_linha,
                            'nome',
                            linha.nome,
                            'erro_bloco',
                            str(exc),
                        )
                    )

            for linha in estrutura.salas:
                _incrementar_progresso()
                try:
                    with transaction.atomic():
                        sala, criado = self._criar_ou_atualizar_sala(linha, mapa_blocos)
                        mapa_salas[linha.sala_id_planilha] = sala
                        if criado:
                            resumo.salas_criadas += 1
                        else:
                            resumo.salas_atualizadas += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            'sala',
                            linha.numero_linha,
                            'nome',
                            linha.nome,
                            'erro_sala',
                            str(exc),
                        )
                    )

            for linha in estrutura.recursos:
                _incrementar_progresso()
                erros_foto = []
                try:
                    with transaction.atomic():
                        recurso, criado = self._criar_ou_atualizar_recurso(
                            linha, mapa_salas
                        )
                        if criado:
                            resumo.recursos_criados += 1
                        else:
                            resumo.recursos_atualizados += 1
                    if linha.foto_url:
                        try:
                            arquivo_foto = baixar_imagem_de_url(linha.foto_url)
                            recurso.business.atualizar_foto(arquivo_foto)
                        except Exception as exc:
                            erros_foto.append(
                                self._criar_erro(
                                    'recurso',
                                    linha.numero_linha,
                                    'foto',
                                    linha.foto_url,
                                    CODIGO_ERRO_FOTO,
                                    str(exc),
                                )
                            )
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            'recurso',
                            linha.numero_linha,
                            'codigo',
                            linha.codigo,
                            'erro_recurso',
                            str(exc),
                        )
                    )
                erros.extend(erros_foto)

            resumo.total_linhas_com_erro = len(
                [erro for erro in erros if erro.codigo != CODIGO_ERRO_FOTO]
            )
            return ResultadoImportacaoDTO(
                sucesso=resumo.total_linhas_com_erro == 0,
                mensagem=(
                    'Importação concluída com sucesso.'
                    if resumo.total_linhas_com_erro == 0
                    else 'Importação concluída com sucesso parcial.'
                ),
                resumo=resumo,
                erros=erros,
                metadados={'modo': 'importacao'},
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar importar_infraestrutura_em_lote.', logger
            )

    def _validar_estrutura_importacao(self, estrutura):
        try:
            if not estrutura.blocos:
                raise ValidationException('A aba "bloco" deve possuir pelo menos um registro.')
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar _validar_estrutura_importacao.', logger
            )

    def _criar_ou_atualizar_bloco(self, linha):
        try:
            from Infraestrutura.blocos.models import Bloco

            self.object_instance.rules.bloco_id_obrigatorio(linha.bloco_id_planilha)
            bloco = Bloco.objects.filter(nome=linha.nome).first()
            if bloco:
                if not bloco.ativo:
                    bloco.business.atualizar_dados({'ativo': True})
                return bloco, False
            bloco = Bloco().business.criar_bloco(nome=linha.nome, ativo=True)
            return bloco, True
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar _criar_ou_atualizar_bloco.', logger
            )

    def _criar_ou_atualizar_sala(self, linha, mapa_blocos):
        try:
            from Infraestrutura.salas.models import Sala

            self.object_instance.rules.sala_id_obrigatorio(linha.sala_id_planilha)
            bloco = obter_bloco_por_id_planilha(linha.bloco_id_planilha, mapa_blocos)
            self.object_instance.rules.bloco_referenciado_existe(bloco)

            sala = Sala.objects.filter(bloco=bloco, nome=linha.nome).first()
            if sala:
                if not sala.ativo:
                    sala.business.atualizar_dados({'ativo': True})
                return sala, False
            sala = Sala().business.criar_sala(
                bloco_id=bloco.pk,
                nome=linha.nome,
                ativo=True,
            )
            return sala, True
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar _criar_ou_atualizar_sala.', logger
            )

    def _criar_ou_atualizar_recurso(self, linha, mapa_salas):
        try:
            from Infraestrutura.recursos.models import Recurso

            self.object_instance.rules.tipo_valido(linha.tipo)
            sala = None
            sala_id = None
            if linha.sala_id_planilha is not None:
                sala = obter_sala_por_id_planilha(linha.sala_id_planilha, mapa_salas)
                self.object_instance.rules.sala_referenciada_existe(sala)
                sala_id = sala.pk

            dados = {
                'tipo': linha.tipo,
                'sala_id': sala_id,
                'descricao': linha.descricao,
                'em_avaria': linha.em_avaria,
                'ativo': True,
            }

            recurso = Recurso.objects.filter(codigo__iexact=linha.codigo).first()
            if recurso:
                recurso.business.atualizar_dados(dados)
                return recurso, False

            recurso = Recurso().business.criar_recurso(
                codigo=linha.codigo,
                **dados,
            )
            return recurso, True
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar _criar_ou_atualizar_recurso.', logger
            )

    def _contar_abas_processadas(self, estrutura):
        try:
            total = 0
            for colecao in [estrutura.blocos, estrutura.salas, estrutura.recursos]:
                if colecao:
                    total += 1
            return total
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar _contar_abas_processadas.', logger
            )

    def _contar_linhas_processadas(self, estrutura):
        try:
            return sum([
                len(estrutura.blocos),
                len(estrutura.salas),
                len(estrutura.recursos),
            ])
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e, 'Não foi possível executar _contar_linhas_processadas.', logger
            )

    def _criar_erro(self, aba, numero_linha, campo, valor, codigo, mensagem):
        try:
            return ErroImportacaoDTO(
                aba=aba,
                numero_linha=numero_linha,
                campo=campo,
                valor=valor,
                codigo=codigo,
                mensagem=mensagem,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _criar_erro.', logger)
