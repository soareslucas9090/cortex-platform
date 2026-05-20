import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import SystemErrorException
from AppCore.common.util.util import normalizar_cpf

from .rules import UsuarioRules

logger = logging.getLogger(__name__)


class UsuarioBusiness(ModelInstanceBusiness):
    """
    Camada de negócio do domínio Usuários.
    Orquestra todas as operações sobre o Usuario e seus sub-recursos
    (Contato, Endereco, Matricula).
    """

    # ------------------------------------------------------------------
    # Operações de criação (sem object_instance)
    # ------------------------------------------------------------------

    def criar_usuario(self, cpf: str, nome: str, password: str, **kwargs):
        """Cria um novo usuário no sistema após validar CPF."""
        from .models import Usuario
        cpf_normalizado = normalizar_cpf(cpf)
        regras = UsuarioRules()
        regras.cpf_formato_valido(cpf_normalizado)
        regras.cpf_unico(cpf_normalizado)
        try:
            return Usuario.objects.create_user(
                cpf=cpf_normalizado,
                password=password,
                nome=nome,
                **kwargs,
            )
        except Exception as e:
            logger.exception('Erro ao criar usuário: %s', e)
            raise SystemErrorException('Não foi possível criar o usuário.')

    # ------------------------------------------------------------------
    # Operações sobre o usuário (dependem de self.object_instance)
    # ------------------------------------------------------------------

    def atualizar_dados(self, dados: dict):
        """Atualiza campos básicos do usuário."""
        try:
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            logger.exception('Erro ao atualizar dados do usuário: %s', e)
            raise SystemErrorException('Não foi possível atualizar os dados do usuário.')

    def atualizar_cpf(self, novo_cpf: str):
        """Atualiza o CPF do usuário com validação de formato e unicidade."""
        cpf_normalizado = normalizar_cpf(novo_cpf)
        regras = UsuarioRules(object_instance=self.object_instance)
        regras.cpf_formato_valido(cpf_normalizado)
        regras.cpf_unico(cpf_normalizado, excluir_id=self.object_instance.pk)
        try:
            self.object_instance.cpf = cpf_normalizado
            self.object_instance.save(update_fields=['cpf'])
        except Exception as e:
            logger.exception('Erro ao atualizar CPF do usuário: %s', e)
            raise SystemErrorException('Não foi possível atualizar o CPF.')

    def desativar(self):
        """Desativa o usuário."""
        regras = UsuarioRules(object_instance=self.object_instance)
        regras.pode_desativar()
        try:
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao desativar usuário: %s', e)
            raise SystemErrorException('Não foi possível desativar o usuário.')

    def reativar(self):
        """Reativa o usuário."""
        regras = UsuarioRules(object_instance=self.object_instance)
        regras.pode_reativar()
        try:
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            logger.exception('Erro ao reativar usuário: %s', e)
            raise SystemErrorException('Não foi possível reativar o usuário.')

    # ------------------------------------------------------------------
    # Operações sobre Contato
    # ------------------------------------------------------------------

    def adicionar_contato(self, email_academico: str = '', email_pessoal: str = '', telefone: str = ''):
        """Adiciona um novo contato ao usuário."""
        from Identidade.contatos.models import Contato
        try:
            return Contato.objects.create(
                usuario=self.object_instance,
                email_academico=email_academico,
                email_pessoal=email_pessoal,
                telefone=telefone,
            )
        except Exception as e:
            logger.exception('Erro ao adicionar contato: %s', e)
            raise SystemErrorException('Não foi possível adicionar o contato.')

    # ------------------------------------------------------------------
    # Operações sobre Endereco
    # ------------------------------------------------------------------

    def salvar_endereco(self, dados: dict):
        """Cria ou atualiza o endereço do usuário (operação idempotente)."""
        from Identidade.enderecos.models import Endereco
        try:
            endereco, _ = Endereco.objects.update_or_create(
                usuario=self.object_instance,
                defaults=dados,
            )
            return endereco
        except Exception as e:
            logger.exception('Erro ao salvar endereço: %s', e)
            raise SystemErrorException('Não foi possível salvar o endereço.')

    # ------------------------------------------------------------------
    # Operações sobre Matricula
    # ------------------------------------------------------------------

    def adicionar_matricula(self, numero_matricula: str):
        """Adiciona uma nova matrícula ao usuário após validar unicidade."""
        from Identidade.matriculas.models import Matricula
        from Identidade.matriculas.choices import SituacaoMatricula
        from Identidade.matriculas.rules import MatriculaRules
        regras = MatriculaRules(object_instance=self.object_instance)
        regras.matricula_nao_duplicada(numero_matricula)
        try:
            return Matricula.objects.create(
                usuario=self.object_instance,
                matricula=numero_matricula,
                situacao=SituacaoMatricula.ATIVA,
            )
        except Exception as e:
            logger.exception('Erro ao adicionar matrícula: %s', e)
            raise SystemErrorException('Não foi possível adicionar a matrícula.')
