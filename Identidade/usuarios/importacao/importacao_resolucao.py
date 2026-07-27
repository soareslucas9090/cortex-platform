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
        sigla = SIGLA_SETOR_ALIASES.get(sigla, sigla)
        return self._get_setores_db().get(sigla)

    def resolver_funcao(self, funcao_id_planilha: str):
        chave = normalizar_id_referencia(funcao_id_planilha)
        if not chave:
            return None

        papel = self.referencias.mapa_funcao_id_para_papel.get(chave)
        if papel is None:
            papel = chave

        funcao = self._get_funcoes_db().get(papel)
        if funcao:
            return funcao

        from Organizacional.funcoes.models import Funcao

        funcao = Funcao.objects.filter(papel_funcao=papel).first()
        if funcao:
            self._get_funcoes_db()[papel] = funcao
        return funcao

    def resolver_cargo(self, cargo_id_planilha: int):
        nome = self.referencias.mapa_cargo_id_para_nome.get(cargo_id_planilha)
        if not nome:
            return None
        return self._get_cargos_db().get(nome.strip())

    def resolver_curso(self, curso_id_planilha: int):
        codigo = self.referencias.mapa_curso_id_para_codigo.get(curso_id_planilha)
        if not codigo:
            return None
        return self._get_cursos_db().get(codigo)

    def resolver_empresa(self, empresa_id_planilha: int):
        nome = self.referencias.mapa_empresa_id_para_nome.get(empresa_id_planilha)
        if not nome:
            return None
        return self._get_empresas_db().get(nome)

    def _get_setores_db(self):
        if self._setores_db is None:
            from Organizacional.setores.models import Setor

            siglas = {
                SIGLA_SETOR_ALIASES.get(sigla, sigla)
                for sigla in self.referencias.mapa_setor_id_para_sigla.values()
            }
            self._setores_db = {
                s.sigla: s for s in Setor.objects.filter(sigla__in=siglas)
            }
        return self._setores_db

    def _get_funcoes_db(self):
        if self._funcoes_db is None:
            from Organizacional.funcoes.models import Funcao

            papeis = set(self.referencias.mapa_funcao_id_para_papel.values())
            self._funcoes_db = {
                f.papel_funcao: f for f in Funcao.objects.filter(papel_funcao__in=papeis)
            }
        return self._funcoes_db

    def _get_cargos_db(self):
        if self._cargos_db is None:
            from PessoasInstitucionais.cargos.models import Cargo

            nomes = {n.strip() for n in self.referencias.mapa_cargo_id_para_nome.values()}
            self._cargos_db = {
                c.nome.strip(): c for c in Cargo.objects.filter(nome__in=nomes)
            }
        return self._cargos_db

    def _get_cursos_db(self):
        if self._cursos_db is None:
            from Academico.cursos.models import Curso

            codigos = set(self.referencias.mapa_curso_id_para_codigo.values())
            self._cursos_db = {
                c.codigo_curso: c for c in Curso.objects.filter(codigo_curso__in=codigos)
            }
        return self._cursos_db

    def _get_empresas_db(self):
        if self._empresas_db is None:
            from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao

            nomes = set(self.referencias.mapa_empresa_id_para_nome.values())
            self._empresas_db = {
                e.nome: e for e in EmpresaInstituicao.objects.filter(nome__in=nomes)
            }
        return self._empresas_db
