class ImportacaoUsuariosException(Exception):
    """Exceção base da importação em lote de usuários."""


class ArquivoImportacaoInvalidoException(ImportacaoUsuariosException):
    """Arquivo ausente, corrompido ou incompatível com a rotina de importação."""


class AbaObrigatoriaAusenteException(ImportacaoUsuariosException):
    """Uma aba obrigatória da planilha não foi encontrada."""


class ColunasObrigatoriasAusentesException(ImportacaoUsuariosException):
    """Uma ou mais colunas obrigatórias da aba não foram encontradas."""


class LinhaImportacaoInvalidaException(ImportacaoUsuariosException):
    """Uma linha da planilha possui valores inválidos ou inconsistentes."""


class ReferenciaInstitucionalNaoEncontradaException(ImportacaoUsuariosException):
    """Uma referência institucional obrigatória não foi encontrada no banco."""


class CardinalidadeImportacaoInvalidaException(ImportacaoUsuariosException):
    """Os relacionamentos internos da planilha possuem cardinalidade inconsistente."""


class MapeamentoInternoInvalidoException(ImportacaoUsuariosException):
    """Não foi possível resolver os vínculos internos entre abas da planilha."""