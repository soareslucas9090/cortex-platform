import logging

from django.db import transaction

from AppCore.core.business.business import ModelInstanceBusiness
from django.db import IntegrityError

from AppCore.core.exceptions.exceptions import (
    BusinessRuleException,
    NotFoundException,
    SystemErrorException,
    ValidationException,
)
from AppCore.common.util.util import normalizar_cpf, normalizar_cep

from Identidade.usuarios.importacao.importacao_parser import ImportacaoUsuariosParser
from Identidade.usuarios.importacao.importacao_resolucao import ImportacaoReferenciasResolver
from Identidade.usuarios.importacao.importacao_dtos import (
    ErroImportacaoDTO,
    ResumoImportacaoDTO,
    ResultadoImportacaoDTO,
)

logger = logging.getLogger(__name__)


class UsuarioBusiness(ModelInstanceBusiness):
    """
    Camada de negócio do domínio Usuários.
    Orquestra todas as operações sobre o Usuario e seus sub-recursos
    (Contato, Endereco, Matricula).
    """

    # ------------------------------------------------------------------
    # Operações de criação (sem object_instance)
    # ------------------------------------------------------------------

    def criar_usuario(
        self, cpf: str = None, matricula: str = None, nome: str = None, password: str = None, **kwargs
    ):
        try:
            """Cria um novo usuário no sistema após validar CPF ou matrícula."""
            from .models import Usuario
            from Identidade.matriculas.models import Matricula
            from Identidade.matriculas.choices import SituacaoMatricula
            cpf_normalizado = None
            if cpf:
                cpf_normalizado = normalizar_cpf(cpf)
                self.object_instance.rules.cpf_formato_valido(cpf_normalizado)
                self.object_instance.rules.cpf_unico(cpf_normalizado)
            else:
                if not matricula:
                    raise ValidationException(
                        'A matrícula é obrigatória caso o CPF não seja informado.'
                    )
                self.object_instance.rules.matricula_nao_duplicada(matricula)
            senha_final = password if password else (cpf_normalizado if cpf_normalizado else matricula)
            with transaction.atomic():
                user = Usuario.objects.create_user(
                    cpf=cpf_normalizado,
                    password=senha_final,
                    nome=nome,
                    **kwargs,
                )
                if matricula:
                    Matricula.objects.create(
                        usuario=user,
                        matricula=matricula,
                        situacao=SituacaoMatricula.ATIVA,
                    )
                return user
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o usuário.', logger)

    # ------------------------------------------------------------------
    # Operações sobre o usuário (dependem de self.object_instance)
    # ------------------------------------------------------------------

    def atualizar_dados(self, dados: dict):
        """Atualiza campos básicos do usuário (sem alterar usuario_coletivo)."""
        try:
            dados.pop('usuario_coletivo', None)
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar os dados do usuário.', logger)

    def definir_flag_coletivo(self, usuario_coletivo: bool):
        """Ativa/desativa a conta coletiva. Ao desativar, limpa o pool."""
        try:
            self.object_instance.usuario_coletivo = usuario_coletivo
            self.object_instance.save(update_fields=['usuario_coletivo'])
            if not usuario_coletivo:
                self.object_instance.empresas_coletivo.clear()
                self.object_instance.cargos_coletivo.clear()
                self.object_instance.funcoes_coletivo.clear()
                self.object_instance.setores_coletivo.clear()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a flag de usuário coletivo.', logger)

    def substituir_associacoes_coletivo(
        self,
        empresas_ids=None,
        cargos_ids=None,
        funcoes_ids=None,
        setores_ids=None,
    ):
        """Substitui o pool completo do usuário coletivo."""
        try:
            self.object_instance.rules.deve_ser_usuario_coletivo()
            empresas_ids = empresas_ids or []
            cargos_ids = cargos_ids or []
            funcoes_ids = funcoes_ids or []
            setores_ids = setores_ids or []
            self.object_instance.rules.validar_ids_associacoes_coletivo(
                empresas_ids=empresas_ids,
                cargos_ids=cargos_ids,
                funcoes_ids=funcoes_ids,
                setores_ids=setores_ids,
            )
            self.object_instance.empresas_coletivo.set(empresas_ids)
            self.object_instance.cargos_coletivo.set(cargos_ids)
            self.object_instance.funcoes_coletivo.set(funcoes_ids)
            self.object_instance.setores_coletivo.set(setores_ids)
            return self.object_instance.helper.obter_configuracao_coletivo()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar as associações do usuário coletivo.', logger)

    def adicionar_associacao_coletiva(self, tipo: str, item_id: int):
        """Adiciona um item ao pool do usuário coletivo."""
        try:
            self.object_instance.rules.deve_ser_usuario_coletivo()
            self.object_instance.rules.validar_item_associacao_coletiva(tipo, item_id)
            relacao = self.object_instance.helper.obter_relacao_coletiva(tipo)
            relacao.add(item_id)
            return self.object_instance.helper.obter_configuracao_coletivo()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível adicionar a associação do usuário coletivo.', logger)

    def remover_associacao_coletiva(self, tipo: str, item_id: int):
        """Remove um item do pool do usuário coletivo."""
        try:
            self.object_instance.rules.deve_ser_usuario_coletivo()
            self.object_instance.rules.associacao_coletiva_existe(tipo, item_id)
            relacao = self.object_instance.helper.obter_relacao_coletiva(tipo)
            relacao.remove(item_id)
            return self.object_instance.helper.obter_configuracao_coletivo()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível remover a associação do usuário coletivo.', logger)

    def atualizar_foto_primaria(self, url: str | None):
        """Atualiza a URL da foto primária do usuário."""
        try:
            self.object_instance.rules.validar_url_foto(url)
            self.object_instance.foto = url or None
            self.object_instance.save(update_fields=['foto'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a foto primária.', logger)

    def atualizar_foto_secundaria(self, arquivo):
        """Envia a foto secundária para o S3 e persiste a chave do objeto."""
        nova_chave = None
        try:
            from AppCore.common.storage.imagens import (
                content_type_por_extensao,
                obter_extensao_pelo_conteudo,
            )
            from Identidade.usuarios.constantes import ANEXO_FOTO_SECUNDARIA
            self.object_instance.rules.validar_arquivo_foto(arquivo)
            extensao = obter_extensao_pelo_conteudo(arquivo)
            chave_antiga = self.object_instance.foto_secundaria
            nova_chave = ANEXO_FOTO_SECUNDARIA.enviar(
                self.object_instance.pk,
                arquivo,
                extensao=extensao,
                content_type=content_type_por_extensao(extensao),
            )
            self.object_instance.foto_secundaria = nova_chave
            self.object_instance.save(update_fields=['foto_secundaria'])
            if chave_antiga and chave_antiga != nova_chave:
                ANEXO_FOTO_SECUNDARIA.remover(chave_antiga)
        except Exception as e:
            if nova_chave:
                from Identidade.usuarios.constantes import ANEXO_FOTO_SECUNDARIA
                ANEXO_FOTO_SECUNDARIA.remover(nova_chave)
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a foto secundária.', logger)

    def remover_foto_secundaria(self):
        """Remove a foto secundária do usuário e tenta apagar o objeto no S3."""
        try:
            from Identidade.usuarios.constantes import ANEXO_FOTO_SECUNDARIA
            chave_antiga = self.object_instance.foto_secundaria
            self.object_instance.foto_secundaria = None
            self.object_instance.save(update_fields=['foto_secundaria'])
            ANEXO_FOTO_SECUNDARIA.remover(chave_antiga)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível remover a foto secundária.', logger)

    def obter_stream_foto_secundaria(self):
        """Obtém o stream e o content-type da foto secundária no S3."""
        try:
            from botocore.exceptions import ClientError

            from Identidade.usuarios.constantes import ANEXO_FOTO_SECUNDARIA
            chave = ANEXO_FOTO_SECUNDARIA.chave_normalizada(
                self.object_instance.foto_secundaria,
            )
            if not chave:
                raise NotFoundException('Foto secundária não encontrada.')
            return ANEXO_FOTO_SECUNDARIA.iterar(chave)
        except ClientError:
            raise NotFoundException('Foto secundária não encontrada.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter a foto secundária.', logger)

    def obter_arquivo_modelo_importacao(self):
        """Obtém o stream e o content-type do modelo ODS de importação no S3."""
        try:
            from botocore.exceptions import ClientError

            from AppCore.common.storage.s3 import iterar_objeto_s3
            from Identidade.usuarios.constantes import CHAVE_MODELO_IMPORTACAO
            return iterar_objeto_s3(
                CHAVE_MODELO_IMPORTACAO,
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

    def atualizar_cpf(self, novo_cpf: str):
        """Atualiza o CPF do usuário com validação de formato e unicidade."""
        try:
            cpf_normalizado = normalizar_cpf(novo_cpf)
            self.object_instance.rules.cpf_formato_valido(cpf_normalizado)
            self.object_instance.rules.cpf_unico(cpf_normalizado, excluir_id=self.object_instance.pk)
            self.object_instance.cpf = cpf_normalizado
            self.object_instance.save(update_fields=['cpf'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o CPF.', logger)

    def desativar(self):
        """Desativa o usuário."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o usuário.', logger)

    def reativar(self):
        """Reativa o usuário."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o usuário.', logger)

    # ------------------------------------------------------------------
    # Operações sobre Contato
    # ------------------------------------------------------------------

    def adicionar_contato(self, email_academico: str = '', email_pessoal: str = '', telefone: str = ''):
        """Adiciona um novo contato ao usuário."""
        try:
            from Identidade.contatos.models import Contato
            return Contato.objects.create(
                usuario=self.object_instance,
                email_academico=email_academico,
                email_pessoal=email_pessoal,
                telefone=telefone,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível adicionar o contato.', logger)

    # ------------------------------------------------------------------
    # Operações sobre Endereco
    # ------------------------------------------------------------------

    def salvar_endereco(self, dados: dict):
        """Cria ou atualiza o endereço do usuário (operação idempotente)."""
        try:
            from Identidade.enderecos.models import Endereco
            endereco, _ = Endereco.objects.update_or_create(
                usuario=self.object_instance,
                defaults=dados,
            )
            return endereco
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível salvar o endereço.', logger)

    # ------------------------------------------------------------------
    # Operações sobre Matricula
    # ------------------------------------------------------------------

    def adicionar_matricula(self, numero_matricula: str):
        """Adiciona uma nova matrícula ao usuário após validar unicidade."""
        try:
            from Identidade.matriculas.models import Matricula
            from Identidade.matriculas.choices import SituacaoMatricula
            self.object_instance.rules.matricula_nao_duplicada(numero_matricula)
            return Matricula.objects.create(
                usuario=self.object_instance,
                matricula=numero_matricula,
                situacao=SituacaoMatricula.ATIVA,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível adicionar a matrícula.', logger)

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
            from .models import ImportacaoLote, StatusImportacao
            from .tasks import processar_importacao_usuarios_task

            self._validar_sem_importacao_em_andamento()

            importacao = ImportacaoLote.objects.create(arquivo=arquivo)

            if not upload_importacao_to_s3(importacao):
                raise SystemErrorException('Não foi possível iniciar a importação.')

            transaction.on_commit(
                lambda: processar_importacao_usuarios_task.delay(importacao.id)
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
        try:
            self._validar_sem_importacao_em_andamento()

            parser = ImportacaoUsuariosParser()
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
                mensagem='Pré-visualização concluída.' if not erros else 'Pré-visualização concluída com pendências.',
                resumo=resumo,
                erros=erros,
                metadados={
                    'modo': 'preview',
                }
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar pre_visualizar_importacao.', logger)

    def importar_usuarios_em_lote(self, importacao_lote):
        try:
            parser = ImportacaoUsuariosParser()
            estrutura = parser.parse(importacao_lote.arquivo)
            self._validar_estrutura_importacao(estrutura)
            resumo = ResumoImportacaoDTO()
            erros = []
            mapa_usuarios = {}
            mapa_alunos = {}
            resolver_referencias = ImportacaoReferenciasResolver(estrutura.referencias)
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
            mapa_matriculas = {
                m.usuario_id_planilha: m.matricula
                for m in estrutura.matriculas
                if m.usuario_id_planilha is not None and m.matricula
            }
            from .models import Usuario
            from Identidade.matriculas.models import Matricula
            cpfs_planilha = []
            for l in estrutura.usuarios:
                if l.cpf:
                    cpf_str = str(l.cpf)
                    cpf_digitos = ''.join(c for c in cpf_str if c.isdigit())
                    if len(cpf_digitos) >= 3:
                        l.cpf = cpf_digitos.zfill(11)
                    cpfs_planilha.append(self.object_instance.helper.normalizar_cpf(l.cpf))
            matriculas_planilha = [m for m in mapa_matriculas.values() if m]
            usuarios_por_cpf = {u.cpf: u for u in Usuario.objects.filter(cpf__in=cpfs_planilha) if u.cpf}
            usuarios_por_matricula = {}
            if matriculas_planilha:
                for m in Matricula.objects.filter(matricula__in=matriculas_planilha).select_related('usuario'):
                    usuarios_por_matricula[m.matricula] = m.usuario
            for linha in estrutura.usuarios:
                _incrementar_progresso()
                try:
                    with transaction.atomic():
                        usuario, criado = self._criar_ou_atualizar_usuario(linha, mapa_matriculas, usuarios_por_cpf, usuarios_por_matricula)
                        mapa_usuarios[linha.usuario_id_planilha] = usuario

                        if usuario.cpf:
                            usuarios_por_cpf[usuario.cpf] = usuario
                        matricula_planilha = mapa_matriculas.get(linha.usuario_id_planilha)
                        if matricula_planilha:
                            usuarios_por_matricula[matricula_planilha] = usuario

                        if criado:
                            resumo.usuarios_criados += 1
                        else:
                            resumo.usuarios_atualizados += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            aba='Usuario',
                            numero_linha=linha.numero_linha,
                            campo='cpf',
                            valor=linha.cpf,
                            codigo='erro_usuario',
                            mensagem=str(exc),
                        )
                    )
            usuarios_ids = [u.id for u in mapa_usuarios.values() if u.id]
            from Identidade.contatos.models import Contato
            contatos_existentes = {c.usuario_id: c for c in Contato.objects.filter(usuario_id__in=usuarios_ids)}
            contatos_to_create, contatos_to_update = {}, {}
            for linha in estrutura.contatos:
                _incrementar_progresso()
                try:
                    usuario = self.object_instance.helper.obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                    self.object_instance.rules.usuario_referenciado_existe(usuario, 'contato')

                    contato = contatos_existentes.get(usuario.id)
                    if contato:
                        contato.email_academico = linha.email_academico
                        contato.email_pessoal = linha.email_pessoal
                        contato.telefone = linha.telefone
                        contato._linha = linha
                        contatos_to_update[usuario.id] = contato
                    elif usuario.id in contatos_to_create:
                        contato = contatos_to_create[usuario.id]
                        contato.email_academico = linha.email_academico
                        contato.email_pessoal = linha.email_pessoal
                        contato.telefone = linha.telefone
                        contato._linha = linha
                    else:
                        novo_contato = Contato(
                            usuario=usuario, email_academico=linha.email_academico,
                            email_pessoal=linha.email_pessoal, telefone=linha.telefone
                        )
                        novo_contato._linha = linha
                        contatos_to_create[usuario.id] = novo_contato
                except Exception as exc:
                    erros.append(self._criar_erro('Contato', linha.numero_linha, 'usuario_id', linha.usuario_id_planilha, 'erro_contato', str(exc)))
            resumo.contatos_atualizados += len(contatos_to_update)
            resumo.contatos_criados += len(contatos_to_create)
            self._executar_bulk_com_fallback(
                Contato, list(contatos_to_update.values()), list(contatos_to_create.values()), ['email_academico', 'email_pessoal', 'telefone'],
                resumo, 'contatos_atualizados', 'contatos_criados', erros, 'Contato', 'usuario_id'
            )
            from Identidade.enderecos.models import Endereco
            enderecos_existentes = {e.usuario_id: e for e in Endereco.objects.filter(usuario_id__in=usuarios_ids)}
            enderecos_to_create, enderecos_to_update = {}, {}
            for linha in estrutura.enderecos:
                _incrementar_progresso()
                try:
                    usuario = self.object_instance.helper.obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                    self.object_instance.rules.usuario_referenciado_existe(usuario, 'endereço')

                    endereco = enderecos_existentes.get(usuario.id)
                    cep_normalizado = normalizar_cep(linha.cep)
                    if endereco:
                        endereco.logradouro = linha.endereco
                        endereco.bairro = linha.bairro
                        endereco.cep = cep_normalizado
                        endereco.complemento = linha.complemento
                        endereco.numero = str(linha.numero or '')
                        endereco.cidade = linha.cidade
                        endereco.estado = linha.estado
                        endereco._linha = linha
                        enderecos_to_update[usuario.id] = endereco
                    elif usuario.id in enderecos_to_create:
                        endereco = enderecos_to_create[usuario.id]
                        endereco.logradouro = linha.endereco
                        endereco.bairro = linha.bairro
                        endereco.cep = cep_normalizado
                        endereco.complemento = linha.complemento
                        endereco.numero = str(linha.numero or '')
                        endereco.cidade = linha.cidade
                        endereco.estado = linha.estado
                        endereco._linha = linha
                    else:
                        novo_endereco = Endereco(
                            usuario=usuario, logradouro=linha.endereco, bairro=linha.bairro,
                            cep=cep_normalizado, complemento=linha.complemento, numero=str(linha.numero or ''),
                            cidade=linha.cidade, estado=linha.estado
                        )
                        novo_endereco._linha = linha
                        enderecos_to_create[usuario.id] = novo_endereco
                except Exception as exc:
                    erros.append(self._criar_erro('Endereco', linha.numero_linha, 'usuario_id', linha.usuario_id_planilha, 'erro_endereco', str(exc)))
            resumo.enderecos_atualizados += len(enderecos_to_update)
            resumo.enderecos_criados += len(enderecos_to_create)
            self._executar_bulk_com_fallback(
                Endereco, list(enderecos_to_update.values()), list(enderecos_to_create.values()),
                ['logradouro', 'bairro', 'cep', 'complemento', 'numero', 'cidade', 'estado'],
                resumo, 'enderecos_atualizados', 'enderecos_criados', erros, 'Endereco', 'usuario_id'
            )
            from Identidade.matriculas.models import Matricula
            matriculas_existentes_qs = Matricula.objects.filter(usuario_id__in=usuarios_ids)
            matriculas_existentes = {(m.usuario_id, m.matricula): m for m in matriculas_existentes_qs}
            matriculas_to_create = []
            matriculas_em_lote = set()
            for linha in estrutura.matriculas:
                _incrementar_progresso()
                try:
                    usuario = self.object_instance.helper.obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                    self.object_instance.rules.usuario_referenciado_existe(usuario, 'matrícula')

                    if linha.matricula in matriculas_em_lote:
                        raise ValidationException(
                            'A matrícula já foi informada para outro usuário nesta importação.'
                        )
                    self.object_instance.rules.matricula_nao_duplicada(linha.matricula)
                    matriculas_em_lote.add(linha.matricula)

                    if (usuario.id, linha.matricula) not in matriculas_existentes:
                        nova_matricula = Matricula(usuario=usuario, matricula=linha.matricula)
                        nova_matricula._linha = linha
                        matriculas_to_create.append(nova_matricula)
                        matriculas_existentes[(usuario.id, linha.matricula)] = nova_matricula
                        resumo.matriculas_criadas += 1
                except Exception as exc:
                    erros.append(self._criar_erro('Matricula', linha.numero_linha, 'usuario_id', linha.usuario_id_planilha, 'erro_matricula', str(exc)))
            self._executar_bulk_com_fallback(
                Matricula, [], matriculas_to_create, [],
                resumo, 'matriculas_atualizadas', 'matriculas_criadas', erros, 'Matricula', 'usuario_id'
            )
            for linha in estrutura.alunos:
                _incrementar_progresso()
                try:
                    with transaction.atomic():
                        usuario = self.object_instance.helper.obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                        self.object_instance.rules.usuario_referenciado_existe(usuario, 'aluno')
                        aluno, criado = self._garantir_aluno(usuario, linha)
                        mapa_alunos[linha.aluno_id_planilha] = aluno
                        if criado:
                            resumo.alunos_criados += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            aba='Aluno',
                            numero_linha=linha.numero_linha,
                            campo='usuario_id',
                            valor=linha.usuario_id_planilha,
                            codigo='erro_aluno',
                            mensagem=str(exc),
                        )
                    )
            for linha in estrutura.servidores:
                _incrementar_progresso()
                try:
                    with transaction.atomic():
                        usuario = self.object_instance.helper.obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                        self.object_instance.rules.usuario_referenciado_existe(usuario, 'servidor')

                        cargo = resolver_referencias.resolver_cargo(linha.cargo_id_planilha)
                        self.object_instance.rules.referencia_seed_existe(cargo, f'cargo_id={linha.cargo_id_planilha}')

                        criado = self._garantir_servidor(usuario, cargo, linha)
                        if criado:
                            resumo.servidores_criados += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            aba='Servidor',
                            numero_linha=linha.numero_linha,
                            campo='cargo_id',
                            valor=linha.cargo_id_planilha,
                            codigo='erro_servidor',
                            mensagem=str(exc),
                        )
                    )
            for linha in estrutura.terceirizados:
                _incrementar_progresso()
                try:
                    with transaction.atomic():
                        usuario = self.object_instance.helper.obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                        self.object_instance.rules.usuario_referenciado_existe(usuario, 'terceirizado')

                        empresa = resolver_referencias.resolver_empresa(linha.empresa_instituicao_id_planilha)
                        self.object_instance.rules.referencia_seed_existe(
                            empresa,
                            f'empresa_instituicao_id={linha.empresa_instituicao_id_planilha}'
                        )

                        criado = self._garantir_terceirizado(usuario, empresa, linha)
                        if criado:
                            resumo.terceirizados_criados += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            aba='Terceirizado',
                            numero_linha=linha.numero_linha,
                            campo='empresa_instituicao_id',
                            valor=linha.empresa_instituicao_id_planilha,
                            codigo='erro_terceirizado',
                            mensagem=str(exc),
                        )
                    )
            for linha in estrutura.setores_lotacao:
                _incrementar_progresso()
                campo_erro = 'usuario_id'
                valor_erro = linha.usuario_id_planilha
                try:
                    with transaction.atomic():
                        usuario = self.object_instance.helper.obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                        self.object_instance.rules.usuario_referenciado_existe(usuario, 'lotação')

                        setor = resolver_referencias.resolver_setor(linha.setor_id_planilha)
                        if not setor:
                            campo_erro = 'setor_id'
                            valor_erro = linha.setor_id_planilha
                        self.object_instance.rules.referencia_seed_existe(setor, f'setor_id={linha.setor_id_planilha}')

                        funcao = None
                        if linha.funcao_id_planilha:
                            funcao = resolver_referencias.resolver_funcao(linha.funcao_id_planilha)
                            if not funcao:
                                campo_erro = 'funcao_id'
                                valor_erro = linha.funcao_id_planilha
                            self.object_instance.rules.referencia_seed_existe(
                                funcao,
                                f'funcao_id={linha.funcao_id_planilha}',
                            )

                        criado = self._garantir_lotacao(usuario, setor, funcao, linha)
                        if criado:
                            resumo.lotacoes_criadas += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            aba='Setor_Lotacao',
                            numero_linha=linha.numero_linha,
                            campo=campo_erro,
                            valor=valor_erro,
                            codigo='erro_lotacao',
                            mensagem=str(exc),
                        )
                    )
            for linha in estrutura.alunos_cursos:
                _incrementar_progresso()
                try:
                    with transaction.atomic():
                        aluno = self.object_instance.helper.obter_aluno_por_id_planilha(linha.aluno_id_planilha, mapa_alunos)
                        self.object_instance.rules.aluno_referenciado_existe(aluno)

                        curso = resolver_referencias.resolver_curso(linha.curso_id_planilha)
                        self.object_instance.rules.referencia_seed_existe(curso, f'curso_id={linha.curso_id_planilha}')

                        criado = self._garantir_vinculo_aluno_curso(aluno, curso, linha)
                        if criado:
                            resumo.vinculos_aluno_curso_criados += 1
                except Exception as exc:
                    erros.append(
                        self._criar_erro(
                            aba='Aluno_Curso',
                            numero_linha=linha.numero_linha,
                            campo='curso_id',
                            valor=linha.curso_id_planilha,
                            codigo='erro_aluno_curso',
                            mensagem=str(exc),
                        )
                    )
            resumo.total_linhas_com_erro = len(erros)
            return ResultadoImportacaoDTO(
                sucesso=len(erros) == 0,
                mensagem='Importação concluída com sucesso.' if not erros else 'Importação concluída com sucesso parcial.',
                resumo=resumo,
                erros=erros,
                metadados={
                    'modo': 'importacao',
                }
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar importar_usuarios_em_lote.', logger)

    def _validar_estrutura_importacao(self, estrutura):
        try:
            if not estrutura.usuarios:
                raise ValidationException('A aba "Usuario" deve possuir pelo menos um registro.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _validar_estrutura_importacao.', logger)

    def _criar_ou_atualizar_usuario(self, linha, mapa_matriculas, usuarios_por_cpf, usuarios_por_matricula):
        try:
            from .models import Usuario
            from Identidade.matriculas.models import Matricula
            self.object_instance.rules.usuario_id_planilha_obrigatorio(linha.usuario_id_planilha)
            cpf_normalizado = None
            matricula_planilha = mapa_matriculas.get(linha.usuario_id_planilha)
            if linha.cpf:
                cpf_digitos = ''.join(c for c in linha.cpf if c.isdigit())
                if len(cpf_digitos) >= 3:
                    linha.cpf = cpf_digitos.zfill(11)

                self.object_instance.rules.cpf_valido_importacao(linha.cpf)
                cpf_normalizado = self.object_instance.helper.normalizar_cpf(linha.cpf)
                usuario = usuarios_por_cpf.get(cpf_normalizado)
            elif matricula_planilha:
                cpf_normalizado = None
                usuario = usuarios_por_matricula.get(matricula_planilha)
            else:
                raise ValidationException('O usuário deve possuir CPF ou Matrícula.')
            if usuario:
                usuario.nome = linha.nome
                usuario.deficiencia = linha.deficiencia
                usuario.ativo = linha.ativo
                usuario.colaborador_externo = linha.colaborador_externo
                if linha.foto:
                    usuario.foto = linha.foto
                if linha.ultimo_login:
                    usuario.last_login = linha.ultimo_login
                usuario.save()
                return usuario, False
            senha_padrao = cpf_normalizado if cpf_normalizado else matricula_planilha
            usuario = Usuario.objects.create_user(
                cpf=cpf_normalizado,
                password=senha_padrao,
                nome=linha.nome,
                deficiencia=linha.deficiencia,
                ativo=linha.ativo,
                colaborador_externo=linha.colaborador_externo,
                foto=linha.foto or None,
                last_login=linha.ultimo_login,
            )
            if matricula_planilha:
                self.object_instance.rules.matricula_nao_duplicada(matricula_planilha)
                Matricula.objects.get_or_create(
                    usuario=usuario,
                    matricula=matricula_planilha,
                )
            return usuario, True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _criar_ou_atualizar_usuario.', logger)

    def _criar_ou_atualizar_contato(self, usuario, linha):
        try:
            from Identidade.contatos.models import Contato
            contato = Contato.objects.filter(usuario=usuario).first()
            if contato:
                contato.email_academico = linha.email_academico
                contato.email_pessoal = linha.email_pessoal
                contato.telefone = linha.telefone
                contato.save()
                return False
            Contato.objects.create(
                usuario=usuario,
                email_academico=linha.email_academico,
                email_pessoal=linha.email_pessoal,
                telefone=linha.telefone,
            )
            return True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _criar_ou_atualizar_contato.', logger)

    def _criar_ou_atualizar_endereco(self, usuario, linha):
        try:
            from Identidade.enderecos.models import Endereco
            endereco = Endereco.objects.filter(usuario=usuario).first()
            cep_normalizado = normalizar_cep(linha.cep)
            if endereco:
                endereco.logradouro = linha.endereco
                endereco.bairro = linha.bairro
                endereco.cep = cep_normalizado
                endereco.complemento = linha.complemento
                endereco.numero = str(linha.numero or '')
                endereco.cidade = linha.cidade
                endereco.estado = linha.estado
                endereco.save()
                return False
            Endereco.objects.create(
                usuario=usuario,
                logradouro=linha.endereco,
                bairro=linha.bairro,
                cep=cep_normalizado,
                complemento=linha.complemento,
                numero=str(linha.numero or ''),
                cidade=linha.cidade,
                estado=linha.estado,
            )
            return True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _criar_ou_atualizar_endereco.', logger)

    def _criar_ou_atualizar_matricula(self, usuario, linha):
        try:
            from Identidade.matriculas.models import Matricula
            matricula = Matricula.objects.filter(usuario=usuario, matricula=linha.matricula).first()
            if matricula:
                return False
            self.object_instance.rules.matricula_nao_duplicada(linha.matricula)
            Matricula.objects.create(
                usuario=usuario,
                matricula=linha.matricula,
            )
            return True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _criar_ou_atualizar_matricula.', logger)

    def _garantir_aluno(self, usuario, linha):
        try:
            from Academico.alunos.models import Aluno
            aluno = Aluno.objects.filter(usuario=usuario).first()
            if aluno:
                if linha.ira is not None:
                    aluno.ira = linha.ira
                    aluno.save()
                return aluno, False
            aluno = Aluno.objects.create(
                usuario=usuario,
                ira=linha.ira if linha.ira is not None else 0,
            )
            return aluno, True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _garantir_aluno.', logger)

    def _garantir_servidor(self, usuario, cargo, linha):
        try:
            from PessoasInstitucionais.servidores.models import Servidor
            servidor = Servidor.objects.filter(usuario=usuario).first()
            from PessoasInstitucionais.servidores.choices import CategoriaServidor
            for categoria in CategoriaServidor.choices:
                if categoria[1] == linha.categoria:
                    categoria = categoria[0]
                    break
            if servidor:
                servidor.cargo = cargo
                servidor.categoria = categoria
                servidor.ativo = linha.ativo
                servidor.save()
                return False
            Servidor.objects.create(
                usuario=usuario,
                cargo=cargo,
                categoria=categoria,
                ativo=linha.ativo,
            )
            return True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _garantir_servidor.', logger)

    def _garantir_terceirizado(self, usuario, empresa, linha):
        try:
            from PessoasInstitucionais.terceirizados.models import Terceirizado
            terceirizado = Terceirizado.objects.filter(usuario=usuario).first()
            if terceirizado:
                terceirizado.empresa_instituicao = empresa
                terceirizado.ativo = linha.ativo
                terceirizado.save()
                return False
            Terceirizado.objects.create(
                usuario=usuario,
                empresa_instituicao=empresa,
                ativo=linha.ativo,
            )
            return True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _garantir_terceirizado.', logger)

    def _garantir_lotacao(self, usuario, setor, funcao, linha):
        """
        Ajustar este método ao model real do app Organizacional.vinculos.
        Caso o nome do model real seja SetorVinculo, esta implementação já tende a funcionar.
        """
        try:
            from Organizacional.vinculos.models import SetorVinculo
            vinculo = SetorVinculo.objects.filter(
                usuario=usuario,
                setor=setor,
                funcao=funcao,
            ).first()
            if vinculo:
                if hasattr(vinculo, 'responsavel'):
                    vinculo.responsavel = linha.responsavel
                vinculo.save()
                return False
            payload = {
                'usuario': usuario,
                'setor': setor,
                'funcao': funcao,
            }
            if hasattr(SetorVinculo, 'responsavel'):
                payload['responsavel'] = linha.responsavel
            SetorVinculo.objects.create(**payload)
            return True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _garantir_lotacao.', logger)

    def _garantir_vinculo_aluno_curso(self, aluno, curso, linha):
        try:
            from Academico.aluno_cursos.models import AlunoCurso
            vinculo = AlunoCurso.objects.filter(aluno=aluno, curso=curso).first()
            if vinculo:
                if linha.ano_conclusao is not None:
                    vinculo.ano_conclusao = linha.ano_conclusao
                    vinculo.save()
                return False
            AlunoCurso.objects.create(
                aluno=aluno,
                curso=curso,
                ano_conclusao=linha.ano_conclusao,
            )
            return True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _garantir_vinculo_aluno_curso.', logger)

    def _contar_abas_processadas(self, estrutura):
        try:
            total = 0
            for colecao in [
                estrutura.usuarios,
                estrutura.contatos,
                estrutura.enderecos,
                estrutura.matriculas,
                estrutura.alunos,
                estrutura.alunos_cursos,
                estrutura.servidores,
                estrutura.terceirizados,
                estrutura.setores_lotacao,
            ]:
                if colecao:
                    total += 1
            return total
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _contar_abas_processadas.', logger)

    def _contar_linhas_processadas(self, estrutura):
        try:
            return sum([
                len(estrutura.usuarios),
                len(estrutura.contatos),
                len(estrutura.enderecos),
                len(estrutura.matriculas),
                len(estrutura.alunos),
                len(estrutura.alunos_cursos),
                len(estrutura.servidores),
                len(estrutura.terceirizados),
                len(estrutura.setores_lotacao),
            ])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _contar_linhas_processadas.', logger)

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

    def _executar_bulk_com_fallback(self, model_class, to_update, to_create, update_fields, resumo, attr_atualizados, attr_criados, erros, aba, campo_erro):
        try:
            if to_update:
                try:
                    with transaction.atomic():
                        model_class.objects.bulk_update(to_update, update_fields)
                except Exception:
                    setattr(resumo, attr_atualizados, getattr(resumo, attr_atualizados) - len(to_update))
                    for obj in to_update:
                        try:
                            with transaction.atomic():
                                obj.save(update_fields=update_fields)
                                setattr(resumo, attr_atualizados, getattr(resumo, attr_atualizados) + 1)
                        except Exception as exc:
                            valor = getattr(obj._linha, f"{campo_erro}_planilha", getattr(obj._linha, campo_erro, None))
                            erros.append(self._criar_erro(aba, obj._linha.numero_linha, campo_erro, valor, f'erro_{aba.lower()}', str(exc)))
            if to_create:
                try:
                    with transaction.atomic():
                        model_class.objects.bulk_create(to_create)
                except Exception:
                    setattr(resumo, attr_criados, getattr(resumo, attr_criados) - len(to_create))
                    for obj in to_create:
                        try:
                            with transaction.atomic():
                                obj.save()
                                setattr(resumo, attr_criados, getattr(resumo, attr_criados) + 1)
                        except Exception as exc:
                            valor = getattr(obj._linha, f"{campo_erro}_planilha", getattr(obj._linha, campo_erro, None))
                            erros.append(self._criar_erro(aba, obj._linha.numero_linha, campo_erro, valor, f'erro_{aba.lower()}', str(exc)))
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar _executar_bulk_com_fallback.', logger)
