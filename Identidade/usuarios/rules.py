import re
from urllib.parse import urlparse

from AppCore.core.rules.rules import ModelInstanceRules
from AppCore.core.exceptions.exceptions import ValidationException
from Identidade.usuarios.fotos.s3_helper import (
    TAMANHO_MAXIMO_FOTO_SECUNDARIA_BYTES,
    TIPOS_IMAGEM_PERMITIDOS,
)


class UsuarioRules(ModelInstanceRules):
    """
    Regras de negócio do domínio Usuários.
    Valida pré-condições para operações sobre o model Usuario.
    Chamada exclusivamente pela camada Business.
    """

    def cpf_valido_importacao(self, cpf: str) -> bool:
        cpf = re.sub(r'\D', '', cpf or '')
        if len(cpf) != 11:
            raise ValidationException('CPF inválido.')
        return True

    def usuario_id_planilha_obrigatorio(self, usuario_id_planilha) -> bool:
        if usuario_id_planilha in (None, ''):
            raise ValidationException('usuario_id da planilha é obrigatório.')
        return True

    def aluno_id_planilha_obrigatorio(self, aluno_id_planilha) -> bool:
        if aluno_id_planilha in (None, ''):
            raise ValidationException('aluno_id da planilha é obrigatório.')
        return True

    def usuario_referenciado_existe(self, usuario, contexto='registro relacionado') -> bool:
        if not usuario:
            raise ValidationException(
                f'Não foi possível localizar o usuário associado ao {contexto}.'
            )
        return True

    def aluno_referenciado_existe(self, aluno, contexto='vínculo aluno-curso') -> bool:
        if not aluno:
            raise ValidationException(
                f'Não foi possível localizar o aluno associado ao {contexto}.'
            )
        return True

    def referencia_seed_existe(self, referencia, nome_referencia: str) -> bool:
        if not referencia:
            raise ValidationException(f'Referência "{nome_referencia}" não encontrada.')
        return True

    def cpf_formato_valido(self, cpf: str) -> bool:
        """Valida que o CPF contém exatamente 11 dígitos numéricos."""
        cpf_limpo = re.sub(r'\D', '', cpf)
        if len(cpf_limpo) != 11:
            self.return_exception('O CPF deve conter exatamente 11 dígitos.')
        return True

    def cpf_unico(self, cpf: str, excluir_id=None) -> bool:
        """Valida que o CPF não está em uso por outro usuário."""
        from .models import Usuario
        qs = Usuario.objects.filter(cpf=cpf)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um usuário cadastrado com esse CPF.')
        return True

    def pode_desativar(self) -> bool:
        """Verifica se o usuário pode ser desativado."""
        if not self.object_instance.ativo:
            self.return_exception('O usuário já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        """Verifica se o usuário pode ser reativado."""
        if self.object_instance.ativo:
            self.return_exception('O usuário já está ativo.')
        return True

    def matricula_nao_duplicada(self, numero_matricula: str, excluir_id=None) -> bool:
        """Valida que o número de matrícula não está duplicado para o mesmo usuário."""
        from Identidade.matriculas.models import Matricula
        qs = Matricula.objects.filter(
            usuario=self.object_instance,
            matricula=numero_matricula,
        )
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('O usuário já possui essa matrícula registrada.')
        return True

    def validar_url_foto(self, url: str | None) -> bool:
        if url in (None, ''):
            return True

        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValidationException('A URL da foto deve usar o esquema http ou https.')
        return True

    def validar_arquivo_foto(self, arquivo) -> bool:
        if arquivo is None:
            raise ValidationException('É necessário enviar um arquivo de imagem.')

        content_type = getattr(arquivo, 'content_type', '') or ''
        if content_type and content_type not in TIPOS_IMAGEM_PERMITIDOS:
            raise ValidationException('Formato de imagem não suportado. Use JPEG, PNG ou WebP.')

        tamanho = getattr(arquivo, 'size', None)
        if tamanho is not None and tamanho > TAMANHO_MAXIMO_FOTO_SECUNDARIA_BYTES:
            raise ValidationException('A imagem deve ter no máximo 3 MB.')
        return True
