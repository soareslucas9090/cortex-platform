from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class ItemRelatorio:
    codigo: str
    descricao: str
    tipo_rotulo: str
    bloco: str
    sala: str
    devolvido_em: datetime | None
    situacao: str


@dataclass
class EmprestimoRelatorio:
    numero: int
    retirada_em: datetime
    solicitante: str
    responsavel: str
    itens: list[ItemRelatorio] = field(default_factory=list)


@dataclass
class FiltroAplicado:
    rotulo: str
    valor: str


@dataclass
class ResumoRelatorio:
    emprestimos: int
    itens: int
    devolvidos: int
    em_aberto: int
    atrasados: int


@dataclass
class DadosRelatorioEmprestimos:
    periodo_inicio: date
    periodo_fim: date
    emitido_em_rotulo: str
    emitido_por: str
    escopo: str
    filtros: list[FiltroAplicado]
    resumo: ResumoRelatorio
    emprestimos: list[EmprestimoRelatorio]