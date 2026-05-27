import logging

from django.db import transaction

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import ValidationException, SystemErrorException
from AppCore.common.util.util import normalizar_cpf

from .rules import UsuarioRules
from .helpers import UsuarioHelpers
from Identidade.usuarios.importacao.importacao_parser import ImportacaoUsuariosParser
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

    def criar_usuario(self, cpf: str = None, matricula: str = None, nome: str = None, password: str = None, **kwargs):
        """Cria um novo usuário no sistema após validar CPF ou matrícula."""
        from .models import Usuario
        from Identidade.matriculas.models import Matricula
        from Identidade.matriculas.choices import SituacaoMatricula
        
        regras = UsuarioRules()
        
        cpf_normalizado = None
        if cpf:
            cpf_normalizado = normalizar_cpf(cpf)
            regras.cpf_formato_valido(cpf_normalizado)
            regras.cpf_unico(cpf_normalizado)
        else:
            if not matricula:
                raise ValidationException('A matrícula é obrigatória caso o CPF não seja informado.')
            if Matricula.objects.filter(matricula=matricula).exists():
                raise ValidationException('Já existe um usuário cadastrado com esta matrícula.')

        # Senha padrão: CPF (se houver) ou matrícula
        senha_final = password if password else (cpf_normalizado if cpf_normalizado else matricula)
        
        try:
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
            logger.exception('Erro ao criar usuário: %s', e)
            raise SystemErrorException('Não foi possível criar o usuário.')

    # ------------------------------------------------------------------
    # Operações sobre o usuário (dependem de self.object_instance)
    # ------------------------------------------------------------------

    def atualizar_dados(self, dados: dict):
        """Atualiza campos básicos do usuário."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar dados do usuário: %s', e)
            raise SystemErrorException('Não foi possível atualizar os dados do usuário.')

    def atualizar_cpf(self, novo_cpf: str):
        """Atualiza o CPF do usuário com validação de formato e unicidade."""
        cpf_normalizado = normalizar_cpf(novo_cpf)
        regras = UsuarioRules(object_instance=self.object_instance)
        regras.cpf_formato_valido(cpf_normalizado)
        regras.cpf_unico(cpf_normalizado, excluir_id=self.object_instance.pk)
        try:
            self.object_instance.cpf = cpf_normalizado
            self.object_instance.save(update_fields=['cpf'])
        except Exception as e:
            logger.exception('Erro ao atualizar CPF do usuário: %s', e)
            raise SystemErrorException('Não foi possível atualizar o CPF.')

    def desativar(self):
        """Desativa o usuário."""
        regras = UsuarioRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar usuário: %s', e)
            raise SystemErrorException('Não foi possível desativar o usuário.')

    def reativar(self):
        """Reativa o usuário."""
        regras = UsuarioRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar usuário: %s', e)
            raise SystemErrorException('Não foi possível reativar o usuário.')

    # ------------------------------------------------------------------
    # Operações sobre Contato
    # ------------------------------------------------------------------

    def adicionar_contato(self, email_academico: str = '', email_pessoal: str = '', telefone: str = ''):
        """Adiciona um novo contato ao usuário."""
        from Identidade.contatos.models import Contato
        try:
            return Contato.objects.create(
                usuario=self.object_instance,
                email_academico=email_academico,
                email_pessoal=email_pessoal,
                telefone=telefone,
            )
        except Exception as e:
            logger.exception('Erro ao adicionar contato: %s', e)
            raise SystemErrorException('Não foi possível adicionar o contato.')

    # ------------------------------------------------------------------
    # Operações sobre Endereco
    # ------------------------------------------------------------------

    def salvar_endereco(self, dados: dict):
        """Cria ou atualiza o endereço do usuário (operação idempotente)."""
        from Identidade.enderecos.models import Endereco
        try:
            endereco, _ = Endereco.objects.update_or_create(
                usuario=self.object_instance,
                defaults=dados,
            )
            return endereco
        except Exception as e:
            logger.exception('Erro ao salvar endereço: %s', e)
            raise SystemErrorException('Não foi possível salvar o endereço.')

    # ------------------------------------------------------------------
    # Operações sobre Matricula
    # ------------------------------------------------------------------

    def adicionar_matricula(self, numero_matricula: str):
        """Adiciona uma nova matrícula ao usuário após validar unicidade."""
        from Identidade.matriculas.models import Matricula
        from Identidade.matriculas.choices import SituacaoMatricula
        from Identidade.matriculas.rules import MatriculaRules
        regras = MatriculaRules(object_instance=self.object_instance)
        regras.matricula_nao_duplicada(numero_matricula)
        try:
            return Matricula.objects.create(
                usuario=self.object_instance,
                matricula=numero_matricula,
                situacao=SituacaoMatricula.ATIVA,
            )
        except Exception as e:
            logger.exception('Erro ao adicionar matrícula: %s', e)
            raise SystemErrorException('Não foi possível adicionar a matrícula.')

    def pre_visualizar_importacao(self, arquivo):
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

    def importar_usuarios_em_lote(self, importacao_lote):
        parser = ImportacaoUsuariosParser()
        estrutura = parser.parse(importacao_lote.arquivo)

        self._validar_estrutura_importacao(estrutura)

        resumo = ResumoImportacaoDTO()
        erros = []
        mapa_usuarios = {}
        mapa_alunos = {}

        resumo.total_abas_processadas = self._contar_abas_processadas(estrutura)
        resumo.total_linhas_processadas = self._contar_linhas_processadas(estrutura)
        
        importacao_lote.total_linhas = resumo.total_linhas_processadas
        importacao_lote.save(update_fields=['total_linhas'])
        
        def _incrementar_progresso():
            importacao_lote.linhas_processadas += 1
            if importacao_lote.linhas_processadas % 100 == 0 or importacao_lote.linhas_processadas == importacao_lote.total_linhas:
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
                cpfs_planilha.append(UsuarioHelpers().normalizar_cpf(l.cpf))
                
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

        # Contatos
        from Identidade.contatos.models import Contato
        contatos_existentes = {c.usuario_id: c for c in Contato.objects.filter(usuario_id__in=usuarios_ids)}
        contatos_to_create, contatos_to_update = {}, {}

        for linha in estrutura.contatos:
            _incrementar_progresso()
            try:
                usuario = UsuarioHelpers().obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                UsuarioRules().usuario_referenciado_existe(usuario, 'contato')

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

        # Enderecos
        from Identidade.enderecos.models import Endereco
        enderecos_existentes = {e.usuario_id: e for e in Endereco.objects.filter(usuario_id__in=usuarios_ids)}
        enderecos_to_create, enderecos_to_update = {}, {}

        for linha in estrutura.enderecos:
            _incrementar_progresso()
            try:
                usuario = UsuarioHelpers().obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                UsuarioRules().usuario_referenciado_existe(usuario, 'endereço')

                endereco = enderecos_existentes.get(usuario.id)
                if endereco:
                    endereco.logradouro = linha.endereco
                    endereco.bairro = linha.bairro
                    endereco.cep = linha.cep
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
                    endereco.cep = linha.cep
                    endereco.complemento = linha.complemento
                    endereco.numero = str(linha.numero or '')
                    endereco.cidade = linha.cidade
                    endereco.estado = linha.estado
                    endereco._linha = linha
                else:
                    novo_endereco = Endereco(
                        usuario=usuario, logradouro=linha.endereco, bairro=linha.bairro,
                        cep=linha.cep, complemento=linha.complemento, numero=str(linha.numero or ''),
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

        # Matriculas
        from Identidade.matriculas.models import Matricula
        matriculas_existentes_qs = Matricula.objects.filter(usuario_id__in=usuarios_ids)
        matriculas_existentes = {(m.usuario_id, m.matricula): m for m in matriculas_existentes_qs}
        matriculas_to_create = []

        for linha in estrutura.matriculas:
            _incrementar_progresso()
            try:
                usuario = UsuarioHelpers().obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                UsuarioRules().usuario_referenciado_existe(usuario, 'matrícula')

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
                    usuario = UsuarioHelpers().obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                    UsuarioRules().usuario_referenciado_existe(usuario, 'aluno')
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

        from PessoasInstitucionais.cargos.models import Cargo
        cargos_ids = {l.cargo_id_planilha for l in estrutura.servidores if l.cargo_id_planilha}
        mapa_cargos_db = {c.id: c for c in Cargo.objects.filter(id__in=cargos_ids)} if cargos_ids else {}

        for linha in estrutura.servidores:
            _incrementar_progresso()
            try:
                with transaction.atomic():
                    usuario = UsuarioHelpers().obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                    UsuarioRules().usuario_referenciado_existe(usuario, 'servidor')

                    cargo = mapa_cargos_db.get(linha.cargo_id_planilha)
                    UsuarioRules().referencia_seed_existe(cargo, f'cargo_id={linha.cargo_id_planilha}')

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

        from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
        empresas_ids = {l.empresa_instituicao_id_planilha for l in estrutura.terceirizados if l.empresa_instituicao_id_planilha}
        mapa_empresas_db = {e.id: e for e in EmpresaInstituicao.objects.filter(id__in=empresas_ids)} if empresas_ids else {}

        for linha in estrutura.terceirizados:
            _incrementar_progresso()
            try:
                with transaction.atomic():
                    usuario = UsuarioHelpers().obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                    UsuarioRules().usuario_referenciado_existe(usuario, 'terceirizado')

                    empresa = mapa_empresas_db.get(linha.empresa_instituicao_id_planilha)
                    UsuarioRules().referencia_seed_existe(
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

        from Organizacional.setores.models import Setor
        from Organizacional.funcoes.models import Funcao
        setores_ids = {l.setor_id_planilha for l in estrutura.setores_lotacao if l.setor_id_planilha}
        funcoes_siglas = {l.funcao_id_planilha for l in estrutura.setores_lotacao if l.funcao_id_planilha}
        mapa_setores_db = {s.id: s for s in Setor.objects.filter(id__in=setores_ids)} if setores_ids else {}
        mapa_funcoes_db = {f.sigla: f for f in Funcao.objects.filter(sigla__in=funcoes_siglas)} if funcoes_siglas else {}

        for linha in estrutura.setores_lotacao:
            _incrementar_progresso()
            try:
                with transaction.atomic():
                    usuario = UsuarioHelpers().obter_usuario_por_id_planilha(linha.usuario_id_planilha, mapa_usuarios)
                    UsuarioRules().usuario_referenciado_existe(usuario, 'lotação')

                    setor = mapa_setores_db.get(linha.setor_id_planilha)
                    UsuarioRules().referencia_seed_existe(setor, f'setor_id={linha.setor_id_planilha}')

                    funcao = mapa_funcoes_db.get(linha.funcao_id_planilha)
                    UsuarioRules().referencia_seed_existe(funcao, f'funcao_id={linha.funcao_id_planilha}')

                    criado = self._garantir_lotacao(usuario, setor, funcao, linha)
                    if criado:
                        resumo.lotacoes_criadas += 1
            except Exception as exc:
                erros.append(
                    self._criar_erro(
                        aba='Setor_Lotacao',
                        numero_linha=linha.numero_linha,
                        campo='usuario_id',
                        valor=linha.usuario_id_planilha,
                        codigo='erro_lotacao',
                        mensagem=str(exc),
                    )
                )

        from Academico.cursos.models import Curso
        cursos_ids = {l.curso_id_planilha for l in estrutura.alunos_cursos if l.curso_id_planilha}
        mapa_cursos_db = {c.id: c for c in Curso.objects.filter(id__in=cursos_ids)} if cursos_ids else {}

        for linha in estrutura.alunos_cursos:
            _incrementar_progresso()
            try:
                with transaction.atomic():
                    aluno = UsuarioHelpers().obter_aluno_por_id_planilha(linha.aluno_id_planilha, mapa_alunos)
                    UsuarioRules().aluno_referenciado_existe(aluno)

                    curso = mapa_cursos_db.get(linha.curso_id_planilha)
                    UsuarioRules().referencia_seed_existe(curso, f'curso_id={linha.curso_id_planilha}')

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

    def _validar_estrutura_importacao(self, estrutura):
        if not estrutura.usuarios:
            raise ValidationException('A aba "Usuario" deve possuir pelo menos um registro.')

    def _criar_ou_atualizar_usuario(self, linha, mapa_matriculas, usuarios_por_cpf, usuarios_por_matricula):
        from .models import Usuario
        from Identidade.matriculas.models import Matricula

        UsuarioRules().usuario_id_planilha_obrigatorio(linha.usuario_id_planilha)
        
        cpf_normalizado = None
        matricula_planilha = mapa_matriculas.get(linha.usuario_id_planilha)

        if linha.cpf:
            cpf_digitos = ''.join(c for c in linha.cpf if c.isdigit())
            if len(cpf_digitos) >= 3:
                linha.cpf = cpf_digitos.zfill(11)

            UsuarioRules().cpf_valido_importacao(linha.cpf)
            cpf_normalizado = UsuarioHelpers().normalizar_cpf(linha.cpf)
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
            if linha.ultimo_login:
                usuario.last_login = linha.ultimo_login
            usuario.save()
            return usuario, False

        # Senha padrão: CPF (se houver) ou matrícula
        senha_padrao = cpf_normalizado if cpf_normalizado else matricula_planilha

        usuario = Usuario.objects.create_user(
            cpf=cpf_normalizado,
            password=senha_padrao,
            nome=linha.nome,
            deficiencia=linha.deficiencia,
            ativo=linha.ativo,
            last_login=linha.ultimo_login,
        )

        if matricula_planilha:
            Matricula.objects.get_or_create(
                usuario=usuario,
                matricula=matricula_planilha,
            )

        return usuario, True

    def _criar_ou_atualizar_contato(self, usuario, linha):
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

    def _criar_ou_atualizar_endereco(self, usuario, linha):
        from Identidade.enderecos.models import Endereco

        endereco = Endereco.objects.filter(usuario=usuario).first()
        if endereco:
            endereco.logradouro = linha.endereco
            endereco.bairro = linha.bairro
            endereco.cep = linha.cep
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
            cep=linha.cep,
            complemento=linha.complemento,
            numero=str(linha.numero or ''),
            cidade=linha.cidade,
            estado=linha.estado,
        )
        return True

    def _criar_ou_atualizar_matricula(self, usuario, linha):
        from Identidade.matriculas.models import Matricula

        matricula = Matricula.objects.filter(usuario=usuario, matricula=linha.matricula).first()
        if matricula:
            return False

        Matricula.objects.create(
            usuario=usuario,
            matricula=linha.matricula,
        )
        return True

    def _garantir_aluno(self, usuario, linha):
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

    def _garantir_servidor(self, usuario, cargo, linha):
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

    def _garantir_terceirizado(self, usuario, empresa, linha):
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

    def _garantir_lotacao(self, usuario, setor, funcao, linha):
        """
        Ajustar este método ao model real do app Organizacional.vinculos.
        Caso o nome do model real seja SetorVinculo, esta implementação já tende a funcionar.
        """
        from Organizacional.vinculos.models import SetorVinculo

        vinculo = SetorVinculo.objects.filter(
            usuario=usuario,
            setor=setor,
            funcao=funcao,
        ).first()

        if vinculo:
            if hasattr(vinculo, 'responsavel'):
                vinculo.responsavel = linha.responsavel
            if hasattr(vinculo, 'monitor'):
                vinculo.monitor = linha.monitor
            vinculo.save()
            return False

        payload = {
            'usuario': usuario,
            'setor': setor,
            'funcao': funcao,
        }

        if hasattr(SetorVinculo, 'responsavel'):
            payload['responsavel'] = linha.responsavel
        if hasattr(SetorVinculo, 'monitor'):
            payload['monitor'] = linha.monitor

        SetorVinculo.objects.create(**payload)
        return True

    def _garantir_vinculo_aluno_curso(self, aluno, curso, linha):
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

    def _contar_abas_processadas(self, estrutura):
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

    def _contar_linhas_processadas(self, estrutura):
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

    def _criar_erro(self, aba, numero_linha, campo, valor, codigo, mensagem):
        return ErroImportacaoDTO(
            aba=aba,
            numero_linha=numero_linha,
            campo=campo,
            valor=valor,
            codigo=codigo,
            mensagem=mensagem,
        )

    def _executar_bulk_com_fallback(self, model_class, to_update, to_create, update_fields, resumo, attr_atualizados, attr_criados, erros, aba, campo_erro):
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
