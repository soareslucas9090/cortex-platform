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