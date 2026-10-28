from AppCore.core.helpers.helpers import ModelInstanceHelpers


class CursoHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todos os cursos ativos."""
        from .models import Curso
        return Curso.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os cursos inativos."""
        from .models import Curso
        return Curso.objects.filter(ativo=False)

    def obter_por_codigo_normalizado(self, codigo_curso):
        """Retorna o curso cujo código coincide após normalização de texto, ou None."""
        from AppCore.common.util.util import normalizar_chave_texto
        from .models import Curso

        chave = normalizar_chave_texto(codigo_curso)
        if not chave:
            return None
        for curso in Curso.objects.all():
            if normalizar_chave_texto(curso.codigo_curso) == chave:
                return curso
        return None
