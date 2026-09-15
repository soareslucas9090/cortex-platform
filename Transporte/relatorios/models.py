from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class RelatorioAlunos(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin):
    """Objeto de domínio somente leitura para composição das camadas do relatório."""

    from .business import RelatorioAlunosBusiness
    from .helpers import RelatorioAlunosHelpers
    from .rules import RelatorioAlunosRules

    business_class = RelatorioAlunosBusiness
    helper_class = RelatorioAlunosHelpers
    rules_class = RelatorioAlunosRules
