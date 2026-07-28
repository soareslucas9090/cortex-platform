import re

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class UsuarioHelpers(ModelInstanceHelpers):
    """
    Queries e utilitários do domínio Usuários.
    Fornece consultas reutilizáveis sobre o model Usuario.
    Chamada exclusivamente pela camada Business.
    """

    def listar_ativos(self):
        """Retorna todos os usuários ativos do sistema."""
        from .models import Usuario
        return Usuario.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os usuários inativos do sistema."""
        from .models import Usuario
        return Usuario.objects.filter(ativo=False)

    def normalizar_cpf(self, cpf: str) -> str:
        if not cpf:
            return ''
        return re.sub(r'\D', '', str(cpf))

    def obter_usuario_por_cpf(self, cpf: str):
        from .models import Usuario

        cpf_normalizado = self.normalizar_cpf(cpf)
        return Usuario.objects.filter(cpf=cpf_normalizado).first()

    def obter_usuario_por_id_planilha(self, usuario_id_planilha: int, mapa_usuarios: dict):
        return mapa_usuarios.get(usuario_id_planilha)

    def obter_aluno_por_id_planilha(self, aluno_id_planilha: int, mapa_alunos: dict):
        return mapa_alunos.get(aluno_id_planilha)

    def obter_curso_por_id_seed(self, curso_id: int):
        from Academico.cursos.models import Curso
        return Curso.objects.filter(pk=curso_id).first()

    def obter_cargo_por_id_seed(self, cargo_id: int):
        from PessoasInstitucionais.cargos.models import Cargo
        return Cargo.objects.filter(pk=cargo_id).first()

    def obter_empresa_por_id_seed(self, empresa_id: int):
        from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
        return EmpresaInstituicao.objects.filter(pk=empresa_id).first()

    def obter_setor_por_id_seed(self, setor_id: int):
        from Organizacional.setores.models import Setor
        return Setor.objects.filter(pk=setor_id).first()

    def obter_funcao_por_papel_seed(self, papel_funcao: str):
        from Organizacional.funcoes.models import Funcao
        return Funcao.objects.filter(papel_funcao=papel_funcao).first()

    def obter_relacao_coletiva(self, tipo: str):
        mapa = {
            'empresa': self.object_instance.empresas_coletivo,
            'cargo': self.object_instance.cargos_coletivo,
            'funcao': self.object_instance.funcoes_coletivo,
            'setor': self.object_instance.setores_coletivo,
        }
        return mapa[tipo]

    def obter_configuracao_coletivo(self) -> dict:
        """Monta payload da tela de configuração do pool coletivo."""
        usuario = self.object_instance
        return {
            'usuario_id': usuario.pk,
            'usuario_coletivo': usuario.usuario_coletivo,
            'empresas': [
                {'id': e.pk, 'nome': e.nome}
                for e in usuario.empresas_coletivo.order_by('nome')
            ],
            'cargos': [
                {'id': c.pk, 'nome': c.nome}
                for c in usuario.cargos_coletivo.order_by('nome')
            ],
            'funcoes': [
                {
                    'id': f.pk,
                    'nome': f.descricao or f.papel_funcao,
                }
                for f in usuario.funcoes_coletivo.order_by('papel_funcao')
            ],
            'setores': [
                {'id': s.pk, 'nome': f'{s.sigla} — {s.nome}'}
                for s in usuario.setores_coletivo.order_by('nome')
            ],
        }

    def listar_responsaveis_do_coletivo(
        self,
        conta,
        *,
        nome=None,
        cpf=None,
        empresa_id=None,
        cargo_id=None,
        setor_id=None,
        funcao_id=None,
        tipo_perfil=None,
    ):
        """
        Usuários elegíveis como responsável de empréstimo para a conta informada.
        Conta não coletiva: apenas o próprio usuário (se ativo e não coletivo).
        Conta coletiva: união do pool definido pelas associações M2M.
        """
        from django.db.models import Q

        from .models import Usuario

        if not conta.usuario_coletivo:
            return Usuario.objects.filter(
                pk=conta.pk,
                ativo=True,
                usuario_coletivo=False,
            )

        empresas = list(conta.empresas_coletivo.values_list('pk', flat=True))
        cargos = list(conta.cargos_coletivo.values_list('pk', flat=True))
        funcoes = list(conta.funcoes_coletivo.values_list('pk', flat=True))
        setores = list(conta.setores_coletivo.values_list('pk', flat=True))

        if not any([empresas, cargos, funcoes, setores]):
            return Usuario.objects.none()

        criterios = Q()
        if empresas:
            criterios |= Q(
                terceirizado__ativo=True,
                terceirizado__empresa_instituicao_id__in=empresas,
            )
        if cargos:
            criterios |= Q(servidor__ativo=True, servidor__cargo_id__in=cargos)
            criterios |= Q(terceirizado__ativo=True, terceirizado__cargo_id__in=cargos)
        if setores:
            criterios |= Q(
                setor_vinculos__setor_id__in=setores,
                setor_vinculos__setor__ativo=True,
            )
        if funcoes:
            criterios |= Q(
                setor_vinculos__funcao_id__in=funcoes,
                setor_vinculos__funcao__ativo=True,
            )

        qs = Usuario.objects.filter(
            criterios,
            ativo=True,
            usuario_coletivo=False,
        ).distinct()

        if nome:
            qs = qs.filter(nome__unaccent__icontains=nome)
        if cpf:
            cpf_limpo = self.normalizar_cpf(cpf)
            if cpf_limpo:
                qs = qs.filter(cpf__icontains=cpf_limpo)
        if empresa_id:
            qs = qs.filter(
                terceirizado__ativo=True,
                terceirizado__empresa_instituicao_id=empresa_id,
            )
        if cargo_id:
            qs = qs.filter(
                Q(servidor__ativo=True, servidor__cargo_id=cargo_id)
                | Q(terceirizado__ativo=True, terceirizado__cargo_id=cargo_id),
            )
        if setor_id:
            qs = qs.filter(
                setor_vinculos__setor_id=setor_id,
                setor_vinculos__setor__ativo=True,
            )
        if funcao_id:
            qs = qs.filter(
                setor_vinculos__funcao_id=funcao_id,
                setor_vinculos__funcao__ativo=True,
            )
        if tipo_perfil:
            tipo = tipo_perfil.lower()
            if tipo in ('servidor',):
                qs = qs.filter(servidor__isnull=False)
            elif tipo in ('terceirizado',):
                qs = qs.filter(terceirizado__isnull=False)

        return qs.order_by('nome')