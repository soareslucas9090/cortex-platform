import logging

from AppCore.core.business.business import ModelInstanceBusiness

logger = logging.getLogger(__name__)


class BloqueioBusiness(ModelInstanceBusiness):

    def listar_bloqueados(self, usuario):
        try:
            from .helpers import BloqueioHelpers

            if not getattr(usuario, 'tem_acesso_elevado', lambda: False)():
                from AppCore.core.exceptions.exceptions import AuthorizationException
                raise AuthorizationException('Acesso administrativo obrigatório.')
            return BloqueioHelpers().listar_bloqueados()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os bloqueios.', logger)

    def obter_detalhe(self, aluno_pk, usuario):
        try:
            from .helpers import BloqueioHelpers

            if not getattr(usuario, 'tem_acesso_elevado', lambda: False)():
                from AppCore.core.exceptions.exceptions import AuthorizationException
                raise AuthorizationException('Acesso administrativo obrigatório.')
            return BloqueioHelpers().obter_detalhe(aluno_pk)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter o bloqueio.', logger)
