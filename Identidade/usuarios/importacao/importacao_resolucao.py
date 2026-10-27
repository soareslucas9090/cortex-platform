from AppCore.common.util.util import normalizar_chave_texto

from .importacao_dtos import ReferenciasImportacaoDTO


SIGLA_SETOR_ALIASES = {
    'NAPNE/FLO': 'NAPNE',
    'CCTDS/FLO': 'CCTDS',
    'COCURADM/F': 'COCURADM',
    'COCENGCIV/': 'COCENGCIV',
    'ECIENCBIO/': 'ECIENCBIO',
}


def normalizar_id_referencia(valor) -> str:
    if valor is None or valor == '':
        return ''
    if isinstance(valor, float) and valor == int(valor):
        return str(int(valor))
    if isinstance(valor, int):
        return str(valor)
    return str(valor).strip()


def _chave_setor(sigla: str) -> str:
    return normalizar_chave_texto(SIGLA_SETOR_ALIASES.get(sigla, sigla))


class ImportacaoReferenciasResolver:
    """
    Resolve IDs temporários da planilha para objetos do banco via chaves naturais
    definidas nas abas de referência.
    """

    def __init__(self, referencias: ReferenciasImportacaoDTO):
        self.referencias = referencias
        self._setores_db = None
        self._funcoes_db = None
        self._cargos_db = None
        self._cursos_db = None
        self._empresas_db = None

    def resolver_setor(self, setor_id_planilha: int):
        sigla = self.referencias.mapa_setor_id_para_sigla.get(setor_id_planilha)
        if not sigla:
            return None
        chave = _chave_setor(sigla)
        if not chave:
            return None
        return self._get_setores_db().get(chave)

    def resolver_funcao(self, funcao_id_planilha: str):
        chave_id = normalizar_id_referencia(funcao_id_planilha)
        if not chave_id:
            return None

        papel = self.referencias.mapa_funcao_id_para_papel.get(chave_id)
        if papel is None:
            papel = chave_id

        chave = normalizar_chave_texto(papel)
        if not chave:
            return None
        return self._get_funcoes_db().get(chave)

    def resolver_cargo(self, cargo_id_planilha: int):
        nome = self.referencias.mapa_cargo_id_para_nome.get(cargo_id_planilha)
        if not nome:
            return None
        chave = normalizar_chave_texto(nome)
        if not chave:
            return None
        return self._get_cargos_db().get(chave)

    def resolver_curso(self, curso_id_planilha: int):
        codigo = self.referencias.mapa_curso_id_para_codigo.get(curso_id_planilha)
        if not codigo:
            return None
        chave = normalizar_chave_texto(codigo)
        if not chave:
            return None
        return self._get_cursos_db().get(chave)

    def registrar_curso(self, codigo_curso: str, curso):
        if not codigo_curso or curso is None:
            return
        chave = normalizar_chave_texto(codigo_curso)
        if not chave:
            return
        self._get_cursos_db()[chave] = curso

    def registrar_setor(self, sigla: str, setor):
        if setor is None:
            return
        chave = _chave_setor(sigla)
        if not chave:
            return
        self._get_setores_db()[chave] = setor

    def registrar_funcao(self, papel_funcao: str, funcao):
        if funcao is None:
            return
        chave = normalizar_chave_texto(papel_funcao)
        if not chave:
            return
        self._get_funcoes_db()[chave] = funcao

    def registrar_cargo(self, nome: str, cargo):
        if cargo is None:
            return
        chave = normalizar_chave_texto(nome)
        if not chave:
            return
        self._get_cargos_db()[chave] = cargo

    def registrar_empresa(self, nome: str, empresa):
        if empresa is None:
            return
        chave = normalizar_chave_texto(nome)
        if not chave:
            return
        self._get_empresas_db()[chave] = empresa

    def resolver_empresa(self, empresa_id_planilha: int):
        nome = self.referencias.mapa_empresa_id_para_nome.get(empresa_id_planilha)
        if not nome:
            return None
        chave = normalizar_chave_texto(nome)
        if not chave:
            return None
        return self._get_empresas_db().get(chave)

    def _get_setores_db(self):
        if self._setores_db is None:
            from Organizacional.setores.models import Setor

            self._setores_db = {}
            for setor in Setor.objects.all():
                chave = _chave_setor(setor.sigla)
                if chave:
                    self._setores_db[chave] = setor
        return self._setores_db

    def _get_funcoes_db(self):
        if self._funcoes_db is None:
            from Organizacional.funcoes.models import Funcao

            self._funcoes_db = {}
            for funcao in Funcao.objects.all():
                chave = normalizar_chave_texto(funcao.papel_funcao)
                if chave:
                    self._funcoes_db[chave] = funcao
        return self._funcoes_db

    def _get_cargos_db(self):
        if self._cargos_db is None:
            from PessoasInstitucionais.cargos.models import Cargo

            self._cargos_db = {}
            for cargo in Cargo.objects.all():
                chave = normalizar_chave_texto(cargo.nome)
                if chave:
                    self._cargos_db[chave] = cargo
        return self._cargos_db

    def _get_cursos_db(self):
        if self._cursos_db is None:
            from Academico.cursos.models import Curso

            self._cursos_db = {}
            for curso in Curso.objects.all():
                chave = normalizar_chave_texto(curso.codigo_curso)
                if chave:
                    self._cursos_db[chave] = curso
        return self._cursos_db

    def _get_empresas_db(self):
        if self._empresas_db is None:
            from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao

            self._empresas_db = {}
            for empresa in EmpresaInstituicao.objects.all():
                chave = normalizar_chave_texto(empresa.nome)
                if chave:
                    self._empresas_db[chave] = empresa
        return self._empresas_db
