from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class RelatorioEmprestimos(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin):
    """Objeto de domínio somente leitura para o relatório PDF de empréstimos."""

    from .business import RelatorioEmprestimosBusiness
    from .helpers import RelatorioEmprestimosHelpers
    from .rules import RelatorioEmprestimosRules

    business_class = RelatorioEmprestimosBusiness
    helper_class = RelatorioEmprestimosHelpers
    rules_class = RelatorioEmprestimosRules