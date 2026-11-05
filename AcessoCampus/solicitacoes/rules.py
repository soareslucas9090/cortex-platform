from datetime import datetime

from AppCore.core.exceptions.exceptions import ValidationException
from AppCore.core.rules.rules import ModelInstanceRules
from Academico.alunos.choices import SituacaoAluno
from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS

from .choices import StatusSolicitacaoAcesso
from .constantes import (
    EXTENSOES_ANEXO_POR_CONTENT_TYPE,
    LIMITE_SOLICITACAO_ENTRADA_MESMO_DIA,
    NOMES_TIPOS_DO_ALUNO,
    TAMANHO_MAXIMO_ANEXO_BYTES,
)
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

    def validar_tipo_ativo(self, tipo) -> bool:
        if tipo is None or not tipo.ativo:
            self.return_exception('Não é possível autorizar com um tipo inativo.')
        return True

    # ------------------------------------------------------------------
    # Pedido do aluno
    # ------------------------------------------------------------------

    def validar_usuario_aluno_ativo_matriculado(self, usuario) -> bool:
        """Somente usuário e aluno ativos, com situação matriculado, pedem acesso."""
        aluno = getattr(usuario, 'aluno', None)
        if not usuario.ativo or aluno is None or not aluno.ativo:
            self.return_exception('Somente um aluno ativo pode solicitar autorização de acesso.')
        if aluno.situacao != SituacaoAluno.MATRICULADO:
            self.return_exception('Somente um aluno matriculado pode solicitar autorização de acesso.')
        return True

    def validar_vinculo_do_aluno(self, vinculo) -> bool:
        """O vínculo informado deve ser do próprio aluno, ativo e de curso de Ensino Médio."""
        if vinculo is None:
            self.return_exception(
                'Vínculo acadêmico não encontrado entre os seus cursos ativos de ensino médio.'
            )
        return True

    def validar_tipo_do_aluno(self, tipo) -> bool:
        """O aluno só pede os tipos-base (entrada e saída), e o tipo precisa estar ativo."""
        if tipo is None or not tipo.eh_base or tipo.nome not in NOMES_TIPOS_DO_ALUNO:
            self.return_exception('O aluno só pode solicitar entrada ou saída do campus.')
        self.validar_tipo_ativo(tipo)
        return True

    def validar_data_do_aluno(self, data_acesso, agora) -> bool:
        """O aluno não pede acesso para uma data que já passou (fuso America/Fortaleza)."""
        if data_acesso < agora.date():
            self.return_exception('A data para autorização de acesso não pode estar no passado.')
        return True

    def validar_prazo_entrada(self, tipo, data_acesso, agora) -> bool:
        """Entrada para o próprio dia só pode ser pedida até 07:00."""
        if (
            tipo.nome == NOME_TIPO_ENTRADA_CAMPUS
            and data_acesso == agora.date()
            and agora.time() > LIMITE_SOLICITACAO_ENTRADA_MESMO_DIA
        ):
            self.return_exception(
                'Solicitações de entrada para hoje só podem ser feitas até as '
                f'{LIMITE_SOLICITACAO_ENTRADA_MESMO_DIA:%H:%M}.'
            )
        return True

    def validar_horario_nao_passado(self, data_acesso, hora_solicitada, agora) -> bool:
        """Para o próprio dia, o horário pedido não pode já ter passado."""
        if data_acesso == agora.date() and hora_solicitada < agora.time().replace(second=0, microsecond=0):
            self.return_exception('O horário para autorização de acesso já passou.')
        return True

    def validar_sem_autorizacao_aceita_do_aluno(self, ja_existe: bool) -> bool:
        """
        Bloqueia o pedido quando o aluno já tem autorização aceita do mesmo tipo no dia
        (pedido dele aceito ou autorização da gestão). Pedidos pendentes não bloqueiam.
        """
        if ja_existe:
            self.return_exception('Você já possui uma autorização aceita deste tipo para esta data.')
        return True

    def validar_anexo(self, arquivo, content_type_detectado) -> bool:
        """Comprovante obrigatório: PDF, JPG ou PNG de até 5 MB, conferido pelo conteúdo."""
        if content_type_detectado not in EXTENSOES_ANEXO_POR_CONTENT_TYPE:
            raise ValidationException('Envie um comprovante em PDF, JPG ou PNG.')
        tamanho = getattr(arquivo, 'size', None)
        if tamanho is not None and tamanho > TAMANHO_MAXIMO_ANEXO_BYTES:
            raise ValidationException('O comprovante deve ter no máximo 5 MB.')
        return True
