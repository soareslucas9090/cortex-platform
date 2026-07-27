from pathlib import Path

from .importacao_constants import (
    ABAS_OPERACIONAIS,
    ABAS_OBRIGATORIAS_MINIMAS,
    ABA_CARGO,
    ABA_CURSO,
    ABA_EMPRESA_INSTITUICAO,
    ABA_FUNCAO,
    ABA_SETOR,
    ALIAS_CABECALHOS_IMPORTACAO,
    COLUNAS_ESPERADAS_POR_ABA,
    EXTENSOES_SUPORTADAS,
)
from .importacao_dtos import (
    ArquivoImportacaoUsuariosDTO,
    LinhaAlunoCursoImportacaoDTO,
    LinhaAlunoImportacaoDTO,
    LinhaContatoImportacaoDTO,
    LinhaEnderecoImportacaoDTO,
    LinhaMatriculaImportacaoDTO,
    LinhaServidorImportacaoDTO,
    LinhaSetorLotacaoImportacaoDTO,
    LinhaTerceirizadoImportacaoDTO,
    LinhaUsuarioImportacaoDTO,
    ReferenciasImportacaoDTO,
)
from .importacao_resolucao import normalizar_id_referencia, SIGLA_SETOR_ALIASES
from .importacao_exceptions import (
    AbaObrigatoriaAusenteException,
    ArquivoImportacaoInvalidoException,
    ColunasObrigatoriasAusentesException,
)

try:
    from pyexcel_ods3 import get_data
except ImportError:  # pragma: no cover
    get_data = None


class ImportacaoUsuariosParser:
    """
    Parser da planilha .ods multiaba de importação em lote de usuários.
    """

    def parse(self, arquivo) -> ArquivoImportacaoUsuariosDTO:
        self._validar_arquivo(arquivo)
        planilha = self._ler_planilha(arquivo)
        self._validar_abas_minimas(planilha)

        resultado = ArquivoImportacaoUsuariosDTO()

        if 'Usuario' in planilha:
            resultado.usuarios = self._parse_usuarios(planilha['Usuario'])

        if 'Contato' in planilha:
            resultado.contatos = self._parse_contatos(planilha['Contato'])

        if 'Endereco' in planilha:
            resultado.enderecos = self._parse_enderecos(planilha['Endereco'])

        if 'Matricula' in planilha:
            resultado.matriculas = self._parse_matriculas(planilha['Matricula'])

        if 'Aluno' in planilha:
            resultado.alunos = self._parse_alunos(planilha['Aluno'])

        if 'Aluno_Curso' in planilha:
            resultado.alunos_cursos = self._parse_alunos_cursos(planilha['Aluno_Curso'])

        if 'Servidor' in planilha:
            resultado.servidores = self._parse_servidores(planilha['Servidor'])

        if 'Terceirizado' in planilha:
            resultado.terceirizados = self._parse_terceirizados(planilha['Terceirizado'])

        if ABA_SETOR in planilha:
            self._parse_referencia_setores(planilha[ABA_SETOR], resultado.referencias)

        if ABA_FUNCAO in planilha:
            self._parse_referencia_funcoes(planilha[ABA_FUNCAO], resultado.referencias)

        if ABA_CARGO in planilha:
            self._parse_referencia_cargos(planilha[ABA_CARGO], resultado.referencias)

        if ABA_CURSO in planilha:
            self._parse_referencia_cursos(planilha[ABA_CURSO], resultado.referencias)

        if ABA_EMPRESA_INSTITUICAO in planilha:
            self._parse_referencia_empresas(planilha[ABA_EMPRESA_INSTITUICAO], resultado.referencias)

        if 'Setor_Lotacao' in planilha:
            resultado.setores_lotacao = self._parse_setores_lotacao(planilha['Setor_Lotacao'])

        return resultado

    def _validar_arquivo(self, arquivo):
        if not arquivo:
            raise ArquivoImportacaoInvalidoException('Arquivo de importação não enviado.')

        suffix = Path(arquivo.name).suffix.lower()
        if suffix not in EXTENSOES_SUPORTADAS:
            raise ArquivoImportacaoInvalidoException(
                f'Extensão "{suffix}" não suportada. Extensões permitidas: {", ".join(EXTENSOES_SUPORTADAS)}.'
            )

        if get_data is None:
            raise ArquivoImportacaoInvalidoException(
                'Biblioteca de leitura .ods não instalada. Instale pyexcel-ods3.'
            )

    def _ler_planilha(self, arquivo):
        try:
            arquivo.seek(0)
            return get_data(arquivo)
        except Exception as exc:
            raise ArquivoImportacaoInvalidoException(
                f'Não foi possível ler o arquivo .ods: {exc}'
            ) from exc

    def _validar_abas_minimas(self, planilha):
        for aba in ABAS_OBRIGATORIAS_MINIMAS:
            if aba not in planilha:
                raise AbaObrigatoriaAusenteException(
                    f'A aba obrigatória "{aba}" não foi encontrada no arquivo.'
                )

    def _extrair_linhas(self, dados_aba, nome_aba):
        if not dados_aba:
            return []

        header_raw = dados_aba[0]
        header = [self._normalizar_cabecalho(valor) for valor in header_raw]

        colunas_esperadas = COLUNAS_ESPERADAS_POR_ABA.get(nome_aba, [])
        ausentes = [col for col in colunas_esperadas if col not in header]
        if ausentes:
            raise ColunasObrigatoriasAusentesException(
                f'A aba "{nome_aba}" não contém as colunas obrigatórias: {", ".join(ausentes)}.'
            )

        linhas = []
        for index, row in enumerate(dados_aba[1:], start=2):
            row_limpo = [self._limpar_valor(v) for v in row]

            item = {}
            for i, coluna in enumerate(header):
                if not coluna:
                    continue
                item[coluna] = row_limpo[i] if i < len(row_limpo) else None

            if self._linha_vazia([item.get(col) for col in colunas_esperadas]):
                continue

            item['numero_linha'] = index
            linhas.append(item)

        return linhas

    def _limpar_valor(self, valor):
        if isinstance(valor, str):
            v_strip = valor.strip()
            v_upper = v_strip.upper()
            if v_upper == 'NULL' or v_strip == '-' or v_strip == '':
                return None
            return v_strip
        return valor

    def _normalizar_cabecalho(self, valor):
        if valor is None:
            return ''

        texto = str(valor).strip()
        if '\n' in texto:
            texto = texto.split('\n')[0].strip()

        if ' (' in texto:
            texto = texto.split(' (')[0].strip()

        texto = texto.lower()
        return ALIAS_CABECALHOS_IMPORTACAO.get(texto, texto)

    def _linha_vazia(self, row):
        return all(valor is None for valor in row)

    def _parse_usuarios(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Usuario')
        return [
            LinhaUsuarioImportacaoDTO(
                numero_linha=linha['numero_linha'],
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                cpf=self._to_str(linha.get('cpf')),
                nome=self._to_str(linha.get('nome')),
                foto=self._to_str(linha.get('foto')),
                deficiencia=self._to_str(linha.get('deficiencia')),
                ativo=self._to_bool(linha.get('ativo'), default=True),
                ultimo_login=linha.get('ultimo_login'),
                colaborador_externo=self._to_bool(linha.get('colaborador_externo'), default=False),
            )
            for linha in linhas
        ]

    def _parse_contatos(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Contato')
        return [
            LinhaContatoImportacaoDTO(
                numero_linha=linha['numero_linha'],
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                email_academico=self._to_str(linha.get('email_academico')),
                email_pessoal=self._to_str(linha.get('email_pessoal')),
                telefone=self._to_str(linha.get('telefone')),
            )
            for linha in linhas
        ]

    def _parse_enderecos(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Endereco')
        return [
            LinhaEnderecoImportacaoDTO(
                numero_linha=linha['numero_linha'],
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                endereco=self._to_str(linha.get('endereco')),
                bairro=self._to_str(linha.get('bairro')),
                cep=self._to_str(linha.get('cep')),
                complemento=self._to_str(linha.get('complemento')),
                numero=linha.get('numero'),
                cidade=self._to_str(linha.get('cidade')),
                estado=self._to_str(linha.get('estado')),
            )
            for linha in linhas
        ]

    def _parse_matriculas(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Matricula')
        return [
            LinhaMatriculaImportacaoDTO(
                numero_linha=linha['numero_linha'],
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                matricula=self._to_str(linha.get('matricula')),
                situacao=self._to_str(linha.get('situacao')),
            )
            for linha in linhas
        ]

    def _parse_alunos(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Aluno')
        return [
            LinhaAlunoImportacaoDTO(
                numero_linha=linha['numero_linha'],
                aluno_id_planilha=self._to_int(linha.get('aluno_id')),
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                ira=linha.get('ira'),
            )
            for linha in linhas
        ]

    def _parse_alunos_cursos(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Aluno_Curso')
        return [
            LinhaAlunoCursoImportacaoDTO(
                numero_linha=linha['numero_linha'],
                aluno_id_planilha=self._to_int(linha.get('aluno_id')),
                curso_id_planilha=self._to_int(linha.get('curso_id')),
                ano_conclusao=linha.get('ano_conclusao'),
            )
            for linha in linhas
        ]

    def _parse_servidores(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Servidor')
        return [
            LinhaServidorImportacaoDTO(
                numero_linha=linha['numero_linha'],
                servidor_id_planilha=self._to_int(linha.get('servidor_id')),
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                cargo_id_planilha=self._to_int(linha.get('cargo_id')),
                categoria=self._to_str(linha.get('categoria')),
                ativo=self._to_bool(linha.get('ativo'), default=True),
            )
            for linha in linhas
        ]

    def _parse_terceirizados(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Terceirizado')
        return [
            LinhaTerceirizadoImportacaoDTO(
                numero_linha=linha['numero_linha'],
                terceirizado_id_planilha=self._to_int(linha.get('terceirizado_id')),
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                empresa_instituicao_id_planilha=self._to_int(linha.get('empresa_instituicao_id')),
                ativo=self._to_bool(linha.get('ativo'), default=True),
            )
            for linha in linhas
        ]

    def _parse_setores_lotacao(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, 'Setor_Lotacao')
        return [
            LinhaSetorLotacaoImportacaoDTO(
                numero_linha=linha['numero_linha'],
                usuario_id_planilha=self._to_int(linha.get('usuario_id')),
                setor_id_planilha=self._to_int(linha.get('setor_id')),
                funcao_id_planilha=normalizar_id_referencia(linha.get('funcao_id')),
                responsavel=self._to_bool(linha.get('responsavel'), default=False),
                monitor=self._to_bool(linha.get('monitor'), default=False),
            )
            for linha in linhas
        ]

    def _parse_referencia_setores(self, dados_aba, referencias: ReferenciasImportacaoDTO):
        for linha in self._extrair_linhas(dados_aba, ABA_SETOR):
            setor_id = self._to_int(linha.get('setor_id'))
            sigla = self._to_str(linha.get('sigla'))
            if setor_id is not None and sigla:
                referencias.mapa_setor_id_para_sigla[setor_id] = SIGLA_SETOR_ALIASES.get(sigla, sigla)

    def _parse_referencia_funcoes(self, dados_aba, referencias: ReferenciasImportacaoDTO):
        for linha in self._extrair_linhas(dados_aba, ABA_FUNCAO):
            funcao_id = normalizar_id_referencia(linha.get('funcao_id'))
            papel = self._to_str(linha.get('papel_funcao'))
            if funcao_id and papel:
                referencias.mapa_funcao_id_para_papel[funcao_id] = papel

    def _parse_referencia_cargos(self, dados_aba, referencias: ReferenciasImportacaoDTO):
        for linha in self._extrair_linhas(dados_aba, ABA_CARGO):
            cargo_id = self._to_int(linha.get('cargo_id'))
            nome = self._to_str(linha.get('nome'))
            if cargo_id is not None and nome:
                referencias.mapa_cargo_id_para_nome[cargo_id] = nome

    def _parse_referencia_cursos(self, dados_aba, referencias: ReferenciasImportacaoDTO):
        for linha in self._extrair_linhas(dados_aba, ABA_CURSO):
            curso_id = self._to_int(linha.get('curso_id'))
            codigo = self._to_str(linha.get('codigo_curso'))
            if curso_id is not None and codigo:
                referencias.mapa_curso_id_para_codigo[curso_id] = codigo

    def _parse_referencia_empresas(self, dados_aba, referencias: ReferenciasImportacaoDTO):
        for linha in self._extrair_linhas(dados_aba, ABA_EMPRESA_INSTITUICAO):
            empresa_id = self._to_int(linha.get('empresa_instituicao_id'))
            nome = self._to_str(linha.get('nome'))
            if empresa_id is not None and nome:
                referencias.mapa_empresa_id_para_nome[empresa_id] = nome

    def _to_str(self, valor):
        if valor is None:
            return ''
        return str(valor).strip()

    def _to_int(self, valor):
        if valor in (None, ''):
            return None
        return int(valor)

    def _to_bool(self, valor, default=False):
        if valor in (None, ''):
            return default

        if isinstance(valor, bool):
            return valor

        texto = str(valor).strip().lower()
        if texto in ('true', '1', 'sim', 's', 'yes'):
            return True
        if texto in ('false', '0', 'nao', 'não', 'n', 'no'):
            return False

        return default