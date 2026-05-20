import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException

from .rules import SetorRules, FuncaoRules, SetorVinculoRules

logger = logging.getLogger(__name__)


class SetorBusiness(ModelInstanceBusiness):

    def criar_setor(self, nome: str, sigla: str, **kwargs):
        """Cria um novo setor validando unicidade de sigla."""
        from .models import Setor
        regras = SetorRules()
        regras.sigla_unica(sigla)
        try:
            return Setor.objects.create(nome=nome, sigla=sigla, **kwargs)
        except Exception as e:
            logger.exception('Erro ao criar setor: %s', e)
            raise SystemErrorException('Não foi possível criar o setor.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do setor. Revalida sigla se estiver nos dados."""
        if 'sigla' in dados:
            regras = SetorRules(object_instance=self.object_instance)
            regras.sigla_unica(dados['sigla'], excluir_id=self.object_instance.pk)
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar setor: %s', e)
            raise SystemErrorException('Não foi possível atualizar o setor.')

    def desativar(self):
        """Desativa o setor. Bloqueado se houver vínculos ativos."""
        regras = SetorRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar setor: %s', e)
            raise SystemErrorException('Não foi possível desativar o setor.')

    def reativar(self):
        """Reativa o setor."""
        regras = SetorRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar setor: %s', e)
            raise SystemErrorException('Não foi possível reativar o setor.')


class FuncaoBusiness(ModelInstanceBusiness):

    def criar_funcao(self, sigla: str, descricao: str, e_gratificada: bool = False, **kwargs):
        """Cria uma nova função validando unicidade de sigla."""
        from .models import Funcao
        regras = FuncaoRules()
        regras.sigla_unica(sigla)
        try:
            return Funcao.objects.create(
                sigla=sigla,
                descricao=descricao,
                e_gratificada=e_gratificada,
                **kwargs,
            )
        except Exception as e:
            logger.exception('Erro ao criar função: %s', e)
            raise SystemErrorException('Não foi possível criar a função.')

    def atualizar_dados(self, dados: dict):
        """Atualiza campos da função. Revalida sigla se estiver nos dados."""
        if 'sigla' in dados:
            regras = FuncaoRules(object_instance=self.object_instance)
            regras.sigla_unica(dados['sigla'], excluir_id=self.object_instance.pk)
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar função: %s', e)
            raise SystemErrorException('Não foi possível atualizar a função.')

    def desativar(self):
        """Desativa a função. Bloqueado se estiver em uso em vínculos."""
        regras = FuncaoRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar função: %s', e)
            raise SystemErrorException('Não foi possível desativar a função.')

    def reativar(self):
        """Reativa a função."""
        regras = FuncaoRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar função: %s', e)
            raise SystemErrorException('Não foi possível reativar a função.')


class SetorVinculoBusiness(ModelInstanceBusiness):

    def criar_vinculo(self, usuario, setor, funcao, responsavel: bool = False):
        """
        Cria um vínculo entre usuário, setor e função.

        Pré-condições verificadas:
        - setor deve estar ativo;
        - função deve estar ativa;
        - combinação (usuario, setor, funcao) deve ser única.

        Nota: a validação de elegibilidade institucional do responsável
        (responsavel deve ser Servidor) será implementada quando o domínio
        PessoasInstitucionais existir.
        """
        from .models import SetorVinculo
        regras = SetorVinculoRules()
        regras.setor_esta_ativo(setor)
        regras.funcao_esta_ativa(funcao)
        regras.vinculo_sem_duplicata(usuario, setor, funcao)
        try:
            return SetorVinculo.objects.create(
                usuario=usuario,
                setor=setor,
                funcao=funcao,
                responsavel=responsavel,
            )
        except Exception as e:
            logger.exception('Erro ao criar vínculo de setor: %s', e)
            raise SystemErrorException('Não foi possível criar o vínculo com o setor.')

    def atualizar_funcao(self, nova_funcao):
        """
        Atualiza a função exercida no vínculo.
        Revalida atividade da nova função e unicidade da nova combinação.
        """
        regras = SetorVinculoRules(object_instance=self.object_instance)
        regras.funcao_esta_ativa(nova_funcao)
        regras.vinculo_sem_duplicata(
            self.object_instance.usuario,
            self.object_instance.setor,
            nova_funcao,
            excluir_id=self.object_instance.pk,
        )
        try:
            self.object_instance.funcao = nova_funcao
            self.object_instance.save(update_fields=['funcao'])
        except Exception as e:
            logger.exception('Erro ao atualizar função do vínculo: %s', e)
            raise SystemErrorException('Não foi possível atualizar a função do vínculo.')

    def definir_como_responsavel(self):
        """
        Marca o vínculo como responsável pelo setor.

        Nota: a validação de elegibilidade institucional (responsavel deve ser Servidor)
        será implementada quando o domínio PessoasInstitucionais existir.
        """
        regras = SetorVinculoRules(object_instance=self.object_instance)
        regras.setor_esta_ativo(self.object_instance.setor)
        try:
            self.object_instance.responsavel = True
            self.object_instance.save(update_fields=['responsavel'])
        except Exception as e:
            logger.exception('Erro ao definir vínculo como responsável: %s', e)
            raise SystemErrorException('Não foi possível definir o responsável do setor.')

    def remover_responsabilidade(self):
        """
        Remove a marcação de responsável do vínculo.
        Bloqueado se este for o único responsável do setor.
        """
        regras = SetorVinculoRules(object_instance=self.object_instance)
        regras.setor_mantem_responsavel(excluir_id=self.object_instance.pk)
        try:
            self.object_instance.responsavel = False
            self.object_instance.save(update_fields=['responsavel'])
        except Exception as e:
            logger.exception('Erro ao remover responsabilidade do vínculo: %s', e)
            raise SystemErrorException('Não foi possível remover a responsabilidade do vínculo.')

    def criar_vinculo_no_setor(self, usuario, setor_pk: int, funcao, responsavel: bool = False):
        """
        Cria um vínculo buscando o setor pelo pk informado na URL.
        Conveniente para views onde o setor vem do contexto da URL.
        """
        from .models import Setor
        from AppCore.core.exceptions.exceptions import NotFoundException
        try:
            setor = Setor.objects.get(pk=setor_pk)
        except Setor.DoesNotExist:
            raise NotFoundException('Setor não encontrado.')
        return self.criar_vinculo(usuario=usuario, setor=setor, funcao=funcao, responsavel=responsavel)

    def encerrar_vinculo(self):
        """
        Remove o vínculo do setor.
        Bloqueado se for responsável e for o único responsável do setor.
        """
        if self.object_instance.responsavel:
            regras = SetorVinculoRules(object_instance=self.object_instance)
            regras.setor_mantem_responsavel(excluir_id=self.object_instance.pk)
        try:
            self.object_instance.delete()
        except Exception as e:
            logger.exception('Erro ao encerrar vínculo de setor: %s', e)
            raise SystemErrorException('Não foi possível encerrar o vínculo com o setor.')
