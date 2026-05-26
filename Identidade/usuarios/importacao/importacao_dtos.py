from dataclasses import dataclass, field
from typing import Any


@dataclass
class LinhaUsuarioImportacaoDTO:
    numero_linha: int
    usuario_id_planilha: int
    cpf: str
    nome: str
    foto: str = ''
    deficiencia: str = ''
    ativo: bool = True
    ultimo_login: Any = None


@dataclass
class LinhaContatoImportacaoDTO:
    numero_linha: int
    usuario_id_planilha: int
    email_academico: str = ''
    email_pessoal: str = ''
    telefone: str = ''


@dataclass
class LinhaEnderecoImportacaoDTO:
    numero_linha: int
    usuario_id_planilha: int
    endereco: str = ''
    bairro: str = ''
    cep: str = ''
    complemento: str = ''
    numero: Any = None
    cidade: str = ''
    estado: str = ''


@dataclass
class LinhaMatriculaImportacaoDTO:
    numero_linha: int
    usuario_id_planilha: int
    matricula: str = ''
    situacao: str = ''


@dataclass
class LinhaAlunoImportacaoDTO:
    numero_linha: int
    aluno_id_planilha: int
    usuario_id_planilha: int
    ira: Any = None


@dataclass
class LinhaAlunoCursoImportacaoDTO:
    numero_linha: int
    aluno_id_planilha: int
    curso_id_planilha: int
    ano_conclusao: Any = None


@dataclass
class LinhaServidorImportacaoDTO:
    numero_linha: int
    servidor_id_planilha: int
    usuario_id_planilha: int
    cargo_id_planilha: int
    categoria: str = ''
    ativo: bool = True


@dataclass
class LinhaTerceirizadoImportacaoDTO:
    numero_linha: int
    terceirizado_id_planilha: int
    usuario_id_planilha: int
    empresa_instituicao_id_planilha: int
    ativo: bool = True


@dataclass
class LinhaSetorLotacaoImportacaoDTO:
    numero_linha: int
    usuario_id_planilha: int
    setor_id_planilha: int
    funcao_id_planilha: str
    responsavel: bool = False
    monitor: bool = False


@dataclass
class ErroImportacaoDTO:
    aba: str
    numero_linha: int
    campo: str
    valor: Any
    codigo: str
    mensagem: str


@dataclass
class ResumoImportacaoDTO:
    total_abas_processadas: int = 0
    total_linhas_processadas: int = 0
    total_linhas_com_erro: int = 0
    usuarios_criados: int = 0
    usuarios_atualizados: int = 0
    contatos_criados: int = 0
    contatos_atualizados: int = 0
    enderecos_criados: int = 0
    enderecos_atualizados: int = 0
    matriculas_criadas: int = 0
    matriculas_atualizadas: int = 0
    alunos_criados: int = 0
    servidores_criados: int = 0
    terceirizados_criados: int = 0
    vinculos_aluno_curso_criados: int = 0
    lotacoes_criadas: int = 0


@dataclass
class ResultadoImportacaoDTO:
    sucesso: bool
    mensagem: str
    resumo: ResumoImportacaoDTO = field(default_factory=ResumoImportacaoDTO)
    erros: list[ErroImportacaoDTO] = field(default_factory=list)
    metadados: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArquivoImportacaoUsuariosDTO:
    usuarios: list[LinhaUsuarioImportacaoDTO] = field(default_factory=list)
    contatos: list[LinhaContatoImportacaoDTO] = field(default_factory=list)
    enderecos: list[LinhaEnderecoImportacaoDTO] = field(default_factory=list)
    matriculas: list[LinhaMatriculaImportacaoDTO] = field(default_factory=list)
    alunos: list[LinhaAlunoImportacaoDTO] = field(default_factory=list)
    alunos_cursos: list[LinhaAlunoCursoImportacaoDTO] = field(default_factory=list)
    servidores: list[LinhaServidorImportacaoDTO] = field(default_factory=list)
    terceirizados: list[LinhaTerceirizadoImportacaoDTO] = field(default_factory=list)
    setores_lotacao: list[LinhaSetorLotacaoImportacaoDTO] = field(default_factory=list)