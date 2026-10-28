from datetime import datetime

from AppCore.core.rules.rules import ModelInstanceRules

from .choices import StatusSolicitacaoAcesso
from .helpers import FUSO_FORTALEZA

MENSAGEM_AUTORIZACAO_JA_ACEITA = 'Este aluno já possui autorização aceita nesta data e neste tipo.'


class SolicitacaoAcessoRules(ModelInstanceRules):

    def validar_alvo_autorizacao(self, aluno_curso_ids, curso_id, turma) -> bool:
        informou_alunos = bool(aluno_curso_ids)
        informou_curso = curso_id is not None
        informou_turma = bool(turma)
        if informou_alunos and (informou_curso or informou_turma):
            self.return_exception('Informe os alunos ou a turma, não os dois.')
        if informou_alunos:
            return True
        if informou_curso and informou_turma:
            return True
        self.return_exception('Informe os alunos ou o curso e a turma.')
        return True

    def validar_vinculos_encontrados(self, quantidade_pedida, quantidade_encontrada) -> bool:
        if quantidade_encontrada == 0 or quantidade_encontrada != quantidade_pedida:
            self.return_exception(
                'Há aluno fora do escopo ou sem vínculo elegível de Ensino Médio.',
            )
        return True

    def validar_turma_com_alunos(self, quantidade) -> bool:
        if quantidade == 0:
            self.return_exception('Nenhum aluno elegível encontrado para esta turma.')
        return True

    def validar_status_pendente(self) -> bool:
        if self.object_instance.status != StatusSolicitacaoAcesso.PENDENTE:
            self.return_exception('Só é possível avaliar uma solicitação pendente.')
        return True

    def validar_data_nao_passada(self, data_acesso) -> bool:
        hoje = datetime.now(FUSO_FORTALEZA).date()
        if data_acesso < hoje:
            self.return_exception('A data da autorização não pode ser anterior a hoje.')
        return True

    def validar_autorizacao_aceita_unica(self, aluno_ids, ja_existe) -> bool:
        if len(set(aluno_ids)) != len(list(aluno_ids)) or ja_existe:
            self.return_exception(MENSAGEM_AUTORIZACAO_JA_ACEITA)
        return True
