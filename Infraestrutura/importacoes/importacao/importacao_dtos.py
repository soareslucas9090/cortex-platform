from dataclasses import dataclass, field
from typing import Any


@dataclass
class LinhaBlocoImportacaoDTO:
    numero_linha: int
    bloco_id_planilha: int
    nome: str


@dataclass
class LinhaSalaImportacaoDTO:
    numero_linha: int
    sala_id_planilha: int
    bloco_id_planilha: int
    nome: str


@dataclass
class LinhaRecursoImportacaoDTO:
    numero_linha: int
    sala_id_planilha: int | None
    descricao: str = ''
    codigo: str = ''
    em_avaria: bool = False
    tipo: str = ''
    foto_url: str = ''


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
    blocos_criados: int = 0
    blocos_atualizados: int = 0
    salas_criadas: int = 0
    salas_atualizadas: int = 0
    recursos_criados: int = 0
    recursos_atualizados: int = 0


@dataclass
class ResultadoImportacaoDTO:
    sucesso: bool
    mensagem: str
    resumo: ResumoImportacaoDTO = field(default_factory=ResumoImportacaoDTO)
    erros: list[ErroImportacaoDTO] = field(default_factory=list)
    metadados: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArquivoImportacaoInfraestruturaDTO:
    blocos: list[LinhaBlocoImportacaoDTO] = field(default_factory=list)
    salas: list[LinhaSalaImportacaoDTO] = field(default_factory=list)
    recursos: list[LinhaRecursoImportacaoDTO] = field(default_factory=list)
