import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

from .choices import SituacaoMatricula

logger = logging.getLogger(__name__)


class MatriculaBusiness(ModelInstanceBusiness):
    """
    Camada de negócio do domínio Matrículas.
    Orquestra operações sobre o model Matricula.
    """

    def desativar(self):
        """Marca a matrícula como inativa."""
        try:
            self.object_instance.situacao = SituacaoMatricula.INATIVA
            self.object_instance.save(update_fields=['situacao'])
        except Exception as e:
            logger.exception('Erro ao desativar matrícula: %s', e)
            raise SystemErrorException('Não foi possível desativar a matrícula.')
