from django.apps import apps

from AppCore.core.exceptions.exceptions import ValidationException
from AppCore.core.rules.rules import ModelInstanceRules
from AppCore.common.storage.imagens import (
    TAMANHO_MAXIMO_IMAGEM_BYTES as TAMANHO_MAXIMO_FOTO_BYTES,
    TIPOS_IMAGEM_PERMITIDOS,
)

from .choices import TipoRecurso
from .constantes import ALTURA_MINIMA_FOTO, LARGURA_MINIMA_FOTO


class RecursoRules(ModelInstanceRules):

    def codigo_unico(self, codigo: str, excluir_id=None) -> bool:
        """Valida que o código de negócio não está em uso por outro recurso."""
        from .models import Recurso
        qs = Recurso.objects.filter(codigo__iexact=codigo)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um recurso cadastrado com esse código.')
        return True

    def validar_sala_por_tipo(self, tipo: str, sala_id=None) -> bool:
        """Chave exige sala; demais tipos aceitam sala opcional."""
        if tipo == TipoRecurso.CHAVE and not sala_id:
            self.return_exception('Recursos do tipo chave devem estar vinculados a uma sala.')
        return True

    def validar_sala_ativa(self, sala_id=None) -> bool:
        """Sala informada deve existir e estar ativa."""
        if sala_id is None:
            return True
        Sala = apps.get_model('salas', 'Sala')
        sala = Sala.objects.filter(pk=sala_id).first()
        if sala is None:
            self.return_exception('Sala informada não encontrada.')
        if not sala.ativo:
            self.return_exception('A sala informada está inativa.')
        return True

    def pode_desativar(self) -> bool:
        """Recurso só pode ser desativado se estiver ativo."""
        if not self.object_instance.ativo:
            self.return_exception('O recurso já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        """Recurso só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O recurso já está ativo.')
        return True

    def validar_arquivo_foto(self, arquivo) -> bool:
        """Valida presença, tipo e tamanho máximo do arquivo de imagem."""
        if arquivo is None:
            raise ValidationException('É necessário enviar um arquivo de imagem.')

        content_type = getattr(arquivo, 'content_type', '') or ''
        if content_type and content_type not in TIPOS_IMAGEM_PERMITIDOS:
            raise ValidationException('Formato de imagem não suportado. Use JPEG, PNG ou WebP.')

        tamanho = getattr(arquivo, 'size', None)
        if tamanho is not None and tamanho > TAMANHO_MAXIMO_FOTO_BYTES:
            raise ValidationException('A imagem deve ter no máximo 3 MB.')
        return True

    def validar_orientacao_retrato(self, largura: int, altura: int) -> bool:
        """A foto original (após EXIF) deve estar na orientação retrato."""
        if altura <= largura:
            raise ValidationException('A foto deve estar na orientação retrato.')
        return True

    def validar_resolucao_minima_foto(self, largura: int, altura: int) -> bool:
        """Após o recorte 3:4, a imagem deve ter no mínimo 480×640 pixels."""
        if largura < LARGURA_MINIMA_FOTO or altura < ALTURA_MINIMA_FOTO:
            raise ValidationException(
                f'A foto deve ter no mínimo {LARGURA_MINIMA_FOTO}×{ALTURA_MINIMA_FOTO} pixels '
                'após o recorte em retrato 3:4.'
            )
        return True
