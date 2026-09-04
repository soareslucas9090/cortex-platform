from AppCore.core.users_permissions.user_permission import UserModelPermission

from Infraestrutura.permissoes.access import usuario_tem_acesso_total_infraestrutura
from Infraestrutura.permissoes.choices import (
    capacidades_infraestrutura_completas,
    capacidades_infraestrutura_vazias,
)
from Infraestrutura.permissoes.models import PermissaoFuncaoInfraestrutura

from .choices import (
    PERMISSAO_CORTEX_EDITAR_EU,
    PERMISSAO_CORTEX_EDITAR_TUDO,
    PERMISSAO_CORTEX_LER_TUDO,
)


class UsuarioPermissions(UserModelPermission):
    """
    Camada de Permissões do Usuário.
    Define as permissões do usuário para os diferentes módulos do frontend.
    """

    def permissoes_cortex(self) -> dict:
        """
        Permissão para o módulo principal (cortex).
        - EDITAR_TUDO: Se o usuário é staff, admin ou superuser.
        - LER_TUDO: Se possui perfil ativo de servidor ou terceirizado.
        - EDITAR_EU: Somente aluno ou qualquer outro caso básico.
        """
        user = self.object_instance
        if not user:
            return {'cortex': PERMISSAO_CORTEX_EDITAR_EU}

        if user.is_staff or user.is_admin or user.is_superuser:
            cortex_perm = PERMISSAO_CORTEX_EDITAR_TUDO
        else:
            tem_servidor_ativo = False
            try:
                tem_servidor_ativo = (
                    hasattr(user, 'servidor')
                    and user.servidor is not None
                    and getattr(user.servidor, 'ativo', False)
                )
            except Exception:
                pass

            tem_terceirizado_ativo = False
            try:
                tem_terceirizado_ativo = (
                    hasattr(user, 'terceirizado')
                    and user.terceirizado is not None
                    and getattr(user.terceirizado, 'ativo', False)
                )
            except Exception:
                pass

            if tem_servidor_ativo or tem_terceirizado_ativo:
                cortex_perm = PERMISSAO_CORTEX_LER_TUDO
            else:
                cortex_perm = PERMISSAO_CORTEX_EDITAR_EU

        return {
            'cortex': cortex_perm,
        }

    def permissoes_infraestrutura(self) -> dict:
        """
        Capacidades do módulo Infraestrutura: união (OR) das flags por função
        (vínculos ativos) e por usuário (PermissaoUsuarioInfraestrutura).
        Admin e superuser recebem acesso total a todas as capacidades.
        """
        user = self.object_instance
        if not user:
            return {'infraestrutura': capacidades_infraestrutura_vazias()}

        if usuario_tem_acesso_total_infraestrutura(user):
            return {'infraestrutura': capacidades_infraestrutura_completas()}

        return {
            'infraestrutura': PermissaoFuncaoInfraestrutura().helper.compilar_do_usuario(user),
        }

    def permissoes_transporte(self) -> dict:
        """
        Capacidades do Transporte para gestão, visão do motorista e solicitação de tickets.
        """
        user = self.object_instance
        if not user:
            return {
                'transporte': {
                    'gerenciar': False,
                    'motorista': False,
                    'reservar': False,
                    'bloqueado': False,
                    'faltas': 0,
                    'bloqueios': 0,
                },
            }
        from Transporte.motoristas.models import Motorista

        gerenciar = bool(user.is_staff or user.is_admin or user.is_superuser)
        motorista = Motorista().helper.usuario_e_motorista_ativo(user)
        reservar = False
        bloqueado = False
        faltas = 0
        bloqueios = 0
        aluno = getattr(user, 'aluno', None)
        if aluno is not None and user.ativo and aluno.ativo:
            from Academico.alunos.choices import SituacaoAluno

            faltas = aluno.faltas
            bloqueado = aluno.is_bloqueado
            bloqueios = aluno.quantidade_bloqueios
            reservar = aluno.situacao == SituacaoAluno.MATRICULADO and not bloqueado

        return {
            'transporte': {
                'gerenciar': gerenciar,
                'reservar': reservar,
                'bloqueado': bloqueado,
                'faltas': faltas,
                'bloqueios': bloqueios,
                'motorista': motorista,
            },
        }
