class ImportacaoInfraestruturaException(Exception):
    """Exceção base da importação em lote de infraestrutura."""


class ArquivoImportacaoInvalidoException(ImportacaoInfraestruturaException):
    """Arquivo ausente, corrompido ou incompatível com a rotina de importação."""


class AbaObrigatoriaAusenteException(ImportacaoInfraestruturaException):
    """Uma aba obrigatória da planilha não foi encontrada."""


class ColunasObrigatoriasAusentesException(ImportacaoInfraestruturaException):
    """Uma ou mais colunas obrigatórias da aba não foram encontradas."""


class LinhaImportacaoInvalidaException(ImportacaoInfraestruturaException):
    """Uma linha da planilha possui valores inválidos ou inconsistentes."""
