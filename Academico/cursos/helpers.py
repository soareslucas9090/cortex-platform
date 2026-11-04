from AppCore.common.util.util import normalizar_chave_texto
from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import Modalidade, NivelEnsino


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
        from .models import Curso

        chave = normalizar_chave_texto(codigo_curso)
        if not chave:
            return None
        for curso in Curso.objects.all():
            if normalizar_chave_texto(curso.codigo_curso) == chave:
                return curso
        return None

    def texto_choice_vazio(self, texto) -> bool:
        """Indica se o texto da planilha representa ausência de valor."""
        if texto is None:
            return True
        texto_str = str(texto).strip()
        if not texto_str:
            return True
        return texto_str == '-' or texto_str.casefold() == 'null'

    def _normalizar_texto_choice(self, texto) -> str:
        chave = normalizar_chave_texto(texto)
        if not chave:
            return ''
        chave = chave.replace('_', ' ').replace('-', ' ')
        chave = chave.replace('\\', '/')
        return ' '.join(chave.split())

    def _resolver_inteiro_choice(self, texto, choices_class):
        if self.texto_choice_vazio(texto):
            return None
        chave_busca = self._normalizar_texto_choice(texto)
        for membro in choices_class:
            for candidato in (str(membro.value), membro.name, membro.label):
                if self._normalizar_texto_choice(candidato) == chave_busca:
                    return membro.value
        return None

    def resolver_nivel_ensino(self, texto):
        """Resolve texto da planilha para inteiro de NivelEnsino ou None."""
        return self._resolver_inteiro_choice(texto, NivelEnsino)

    def resolver_modalidade(self, texto):
        """Resolve texto da planilha para inteiro de Modalidade ou None."""
        return self._resolver_inteiro_choice(texto, Modalidade)
