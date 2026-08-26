from AppCore.core.exceptions.exceptions import ValidationException
from AppCore.core.rules.rules import ModelInstanceRules

from .importacao.importacao_constants import TIPOS_RECURSO_VALIDOS


class ImportacaoLoteRules(ModelInstanceRules):
    """Regras de validação da importação em lote de infraestrutura."""

    def bloco_id_obrigatorio(self, bloco_id_planilha) -> bool:
        if bloco_id_planilha in (None, ''):
            raise ValidationException('bloco_id da planilha é obrigatório.')
        return True

    def sala_id_obrigatorio(self, sala_id_planilha) -> bool:
        if sala_id_planilha in (None, ''):
            raise ValidationException('sala_id da planilha é obrigatório.')
        return True

    def tipo_valido(self, tipo: str) -> bool:
        if tipo not in TIPOS_RECURSO_VALIDOS:
            raise ValidationException(
                f'Tipo de recurso inválido: {tipo}. Valores aceitos: {", ".join(TIPOS_RECURSO_VALIDOS)}.'
            )
        return True

    def bloco_referenciado_existe(self, bloco, contexto='sala') -> bool:
        if not bloco:
            raise ValidationException(
                f'Não foi possível localizar o bloco associado ao {contexto}.'
            )
        return True

    def sala_referenciada_existe(self, sala, contexto='recurso') -> bool:
        if not sala:
            raise ValidationException(
                f'Não foi possível localizar a sala associada ao {contexto}.'
            )
        return True
