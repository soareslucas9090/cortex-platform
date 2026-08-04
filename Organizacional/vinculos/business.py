import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class SetorVinculoBusiness(ModelInstanceBusiness):

    def criar_vinculo(self, usuario, setor, funcao, responsavel: bool = False):
        """
        Cria um vínculo entre usuário, setor e função.

        Pré-condições verificadas:
        - setor deve estar ativo;
        - função deve estar ativa;
        - combinação (usuario, setor, funcao) deve ser única.

        Nota: a validação de elegibilidade institucional do responsável
        (responsavel deve ser Servidor) é garantida por regra do domínio.
        """
        try:
            from .models import SetorVinculo
            self.object_instance.rules.setor_esta_ativo(setor)
            self.object_instance.rules.funcao_esta_ativa(funcao)
            self.object_instance.rules.vinculo_sem_duplicata(usuario, setor, funcao)
            self.object_instance.rules.usuario_e_aluno_se_exigido(usuario, funcao)
            if responsavel:
                self.object_instance.rules.usuario_e_servidor(usuario)
            return SetorVinculo.objects.create(
                usuario=usuario,
                setor=setor,
                funcao=funcao,
                responsavel=responsavel,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o vínculo com o setor.', logger)

    def atualizar_funcao(self, nova_funcao):
        """
        Atualiza a função exercida no vínculo.
        Revalida atividade da nova função e unicidade da nova combinação.
        """
        try:
            self.object_instance.rules.funcao_esta_ativa(nova_funcao)
            self.object_instance.rules.vinculo_sem_duplicata(
                self.object_instance.usuario,
                self.object_instance.setor,
                nova_funcao,
                excluir_id=self.object_instance.pk,
            )
            self.object_instance.rules.usuario_e_aluno_se_exigido(
                self.object_instance.usuario,
                nova_funcao,
            )
            self.object_instance.funcao = nova_funcao
            self.object_instance.save(update_fields=['funcao'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar a função do vínculo.', logger)

    def definir_como_responsavel(self):
        """
        Marca o vínculo como responsável pelo setor.

        Nota: a validação de elegibilidade institucional (responsavel deve ser Servidor)
        é garantida por regra do domínio.
        """
        try:
            self.object_instance.rules.setor_esta_ativo(self.object_instance.setor)
            self.object_instance.rules.usuario_e_servidor(self.object_instance.usuario)
            self.object_instance.responsavel = True
            self.object_instance.save(update_fields=['responsavel'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível definir o responsável do setor.', logger)

    def remover_responsabilidade(self):
        """
        Remove a marcação de responsável do vínculo.
        Bloqueado se este for o único responsável do setor.
        """
        try:
            self.object_instance.rules.setor_mantem_responsavel(excluir_id=self.object_instance.pk)
            self.object_instance.responsavel = False
            self.object_instance.save(update_fields=['responsavel'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível remover a responsabilidade do vínculo.', logger)

    def criar_vinculo_no_setor(self, usuario, setor_pk: int, funcao, responsavel: bool = False):
        """
        Cria um vínculo buscando o setor pelo pk informado na URL.
        Conveniente para views onde o setor vem do contexto da URL.
        """
        try:
            from Organizacional.setores.models import Setor
            try:
                setor = Setor.objects.get(pk=setor_pk)
            except Setor.DoesNotExist:
                raise NotFoundException('Setor não encontrado.')
            return self.criar_vinculo(usuario=usuario, setor=setor, funcao=funcao, responsavel=responsavel)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível executar criar_vinculo_no_setor.', logger)

    def encerrar_vinculo(self):
        """
        Remove o vínculo do setor.
        Bloqueado se for responsável e for o único responsável do setor.
        """
        try:
            if self.object_instance.responsavel:
                self.object_instance.rules.setor_mantem_responsavel(excluir_id=self.object_instance.pk)
            self.object_instance.delete()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível encerrar o vínculo com o setor.', logger)
