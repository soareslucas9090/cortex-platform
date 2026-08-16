import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import ValidationException

logger = logging.getLogger(__name__)


class RecursoBusiness(ModelInstanceBusiness):

    def criar_recurso(
        self,
        codigo: str,
        tipo: str,
        sala_id=None,
        descricao: str = '',
        **kwargs,
    ):
        """Cria um novo recurso validando código e regras por tipo."""
        try:
            from .models import Recurso
            foto = kwargs.pop('foto', None)
            self.object_instance.rules.codigo_unico(codigo)
            self.object_instance.rules.validar_sala_por_tipo(tipo, sala_id)
            self.object_instance.rules.validar_sala_ativa(sala_id)
            recurso = Recurso.objects.create(
                codigo=codigo,
                tipo=tipo,
                sala_id=sala_id,
                descricao=descricao,
                **kwargs,
            )
            if foto:
                recurso.business.atualizar_foto(foto)
            return recurso
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o recurso.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do recurso. Revalida código e sala por tipo."""
        try:
            tipo = dados.get('tipo', self.object_instance.tipo)
            sala = dados.get('sala', self.object_instance.sala_id)
            sala_id = sala.pk if hasattr(sala, 'pk') else sala
            if 'codigo' in dados:
                self.object_instance.rules.codigo_unico(
                    dados['codigo'],
                    excluir_id=self.object_instance.pk,
                )
            self.object_instance.rules.validar_sala_por_tipo(tipo, sala_id)
            self.object_instance.rules.validar_sala_ativa(sala_id)
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o recurso.', logger)

    def desativar(self):
        """Desativa o recurso (sem exclusão física de negócio)."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o recurso.', logger)

    def reativar(self):
        """Reativa o recurso."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o recurso.', logger)

    def atualizar_foto(self, arquivo):
        """Processa a foto (retrato 3:4), envia ao S3 e persiste a chave."""
        try:
            from AppCore.common.storage.imagens import (
                abrir_imagem,
                recortar_central,
                reencode_jpeg,
            )
            from AppCore.common.storage.s3 import enviar_arquivo_s3, remover_objeto_s3
            from .foto import (
                PREFIXO_S3,
                PROPORCAO_ALTURA,
                PROPORCAO_LARGURA,
            )
            self.object_instance.rules.validar_arquivo_foto(arquivo)
            imagem = abrir_imagem(arquivo)
            largura, altura = imagem.size
            self.object_instance.rules.validar_orientacao_retrato(largura, altura)
            recortada = recortar_central(imagem, PROPORCAO_LARGURA, PROPORCAO_ALTURA)
            largura_final, altura_final = recortada.size
            self.object_instance.rules.validar_resolucao_minima_foto(largura_final, altura_final)
            processada = reencode_jpeg(recortada)
            chave_antiga = self.object_instance.foto
            nova_chave = enviar_arquivo_s3(
                PREFIXO_S3,
                self.object_instance.pk,
                processada,
                extensao='jpg',
                content_type='image/jpeg',
            )
            self.object_instance.foto = nova_chave
            self.object_instance.save(update_fields=['foto'])
            if chave_antiga and chave_antiga != nova_chave:
                remover_objeto_s3(chave_antiga, prefixo=PREFIXO_S3)
        except ValueError as e:
            raise ValidationException(str(e))
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a foto do recurso.', logger)

    def remover_foto(self):
        """Remove a foto do recurso e tenta apagar o objeto no S3."""
        try:
            from AppCore.common.storage.s3 import remover_objeto_s3
            from .foto import PREFIXO_S3
            chave_antiga = self.object_instance.foto
            self.object_instance.foto = None
            self.object_instance.save(update_fields=['foto'])
            if chave_antiga:
                remover_objeto_s3(chave_antiga, prefixo=PREFIXO_S3)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível remover a foto do recurso.', logger)
