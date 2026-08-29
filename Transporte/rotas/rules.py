from AppCore.core.rules.rules import ModelInstanceRules

from .choices import DiaSemana

MENSAGEM_ROTA_DUPLICADA = (
    'Já existe uma rota com este percurso, dia da semana e horário de saída.'
)


class RotaRules(ModelInstanceRules):

    def validar_percurso_ativo(self, percurso_id: int) -> bool:
        """Valida que o percurso existe e está ativo."""
        from Transporte.percursos.models import Percurso
        percurso = Percurso.objects.get(pk=percurso_id)
        if not percurso.ativo:
            self.return_exception('Não é possível vincular a rota a um percurso inativo.')
        return True

    def validar_quantidade_vagas(self, quantidade_vagas: int) -> bool:
        """Valida que a quantidade de vagas é pelo menos 1."""
        if quantidade_vagas is None or quantidade_vagas < 1:
            self.return_exception('A quantidade de vagas deve ser pelo menos 1.')
        return True

    def validar_dia_semana(self, dia_semana: str) -> bool:
        """Valida o dia da semana informado."""
        valores = {choice.value for choice in DiaSemana}
        if dia_semana not in valores:
            self.return_exception('Dia da semana inválido.')
        return True

    def validar_rota_unica(
        self,
        percurso_id: int,
        dia_semana: str,
        horario_saida,
        excluir_id=None,
    ) -> bool:
        """Valida unicidade de percurso + dia + horário."""
        from .models import Rota
        qs = Rota.objects.filter(
            percurso_id=percurso_id,
            dia_semana=dia_semana,
            horario_saida=horario_saida,
        )
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception(MENSAGEM_ROTA_DUPLICADA)
        return True

    def pode_desativar(self) -> bool:
        """Rota só pode ser desativada se já estiver ativa."""
        if not self.object_instance.ativo:
            self.return_exception('A rota já está inativa.')
        return True

    def pode_reativar(self) -> bool:
        """Rota só pode ser reativada se estiver inativa e o percurso estiver ativo."""
        if self.object_instance.ativo:
            self.return_exception('A rota já está ativa.')
        if not self.object_instance.percurso.ativo:
            self.return_exception('Não é possível reativar uma rota cujo percurso está inativo.')
        return True
