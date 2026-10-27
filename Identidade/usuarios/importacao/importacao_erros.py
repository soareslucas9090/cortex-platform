from dataclasses import asdict, is_dataclass

from .importacao_constants import (
    ABA_ALUNO,
    ABA_CARGO,
    ABA_CURSO,
    ABA_EMPRESA_INSTITUICAO,
    ABA_FUNCAO,
    ABA_SETOR,
    ABA_USUARIO,
    ATTR_ID_PLANILHA_POR_ABA,
    CODIGO_ERRO_REFERENCIA_NAO_ENCONTRADA,
    COLECAO_POR_ABA,
    DEPENDENCIAS_DE_LINHA,
    MAX_ERROS_PLANOS_API,
    MAX_GRUPOS_ERRO_API,
    MAX_IMPACTOS_POR_GRUPO_API,
    PAPEL_ERRO_CAUSA,
    PAPEL_ERRO_IMPACTO,
    TIPO_GRUPO_FALHA_ENTIDADE,
    TIPO_GRUPO_LINHA,
    TIPO_GRUPO_REFERENCIA_INEXISTENTE,
)
from .importacao_dtos import (
    CausaErroImportacaoDTO,
    ErroImportacaoDTO,
    GrupoErroImportacaoDTO,
    ImpactoErroImportacaoDTO,
)
from .importacao_resolucao import normalizar_id_referencia


def id_grupo_entidade(aba, id_planilha) -> str:
    return f'{aba}:{normalizar_id_referencia(id_planilha)}'


def id_grupo_referencia(aba, id_planilha) -> str:
    return f'ref:{aba}:{normalizar_id_referencia(id_planilha)}'


def id_grupo_linha(aba, numero_linha) -> str:
    return f'linha:{aba}:{numero_linha}'


def id_planilha_da_linha(aba, linha):
    attr = ATTR_ID_PLANILHA_POR_ABA.get(aba)
    if not attr:
        return None
    return getattr(linha, attr, None)


def serializar_resultado_importacao(resultado) -> dict:
    grupos = getattr(resultado, 'grupos_erro', None) or []
    return {
        'resumo': asdict(resultado.resumo) if is_dataclass(resultado.resumo) else resultado.resumo,
        'erros': [
            asdict(erro) if is_dataclass(erro) else erro
            for erro in resultado.erros
        ],
        'grupos_erro': [
            asdict(grupo) if is_dataclass(grupo) else grupo
            for grupo in grupos
        ],
    }


def truncar_resultado_json(res):
    if not res or not isinstance(res, dict):
        return res

    avisos = []
    res = dict(res)

    grupos = res.get('grupos_erro')
    if isinstance(grupos, list) and len(grupos) > MAX_GRUPOS_ERRO_API:
        omitidos = len(grupos) - MAX_GRUPOS_ERRO_API
        grupos = grupos[:MAX_GRUPOS_ERRO_API]
        avisos.append(
            f'Foram omitidos {omitidos} grupos de erro devido ao tamanho da resposta. '
            f'Apenas os primeiros {MAX_GRUPOS_ERRO_API} estão sendo exibidos.'
        )

    if isinstance(grupos, list):
        grupos_truncados = []
        for grupo in grupos:
            if not isinstance(grupo, dict):
                grupos_truncados.append(grupo)
                continue
            grupo = dict(grupo)
            impactos = grupo.get('impactos') or []
            total_impactos = grupo.get('total_impactos', len(impactos))
            if isinstance(impactos, list) and len(impactos) > MAX_IMPACTOS_POR_GRUPO_API:
                grupo['impactos'] = impactos[:MAX_IMPACTOS_POR_GRUPO_API]
            grupo['total_impactos'] = total_impactos
            grupos_truncados.append(grupo)
        res['grupos_erro'] = grupos_truncados

    erros = res.get('erros')
    if isinstance(erros, list) and len(erros) > MAX_ERROS_PLANOS_API:
        omitidos = len(erros) - MAX_ERROS_PLANOS_API
        res['erros'] = erros[:MAX_ERROS_PLANOS_API]
        avisos.append(
            f'Foram omitidos {omitidos} erros devido ao tamanho da resposta. '
            f'Apenas os primeiros {MAX_ERROS_PLANOS_API} estão sendo exibidos.'
        )

    if avisos:
        res['mensagem_aviso'] = ' '.join(avisos)
    return res


class ColetorErrosImportacao:
    """Acumula erros de importação e agrupa impactos pela causa raiz."""

    def __init__(self, estrutura=None):
        self._estrutura = estrutura
        self._erros = []
        self._grupos_ordem = []
        self._grupos = {}
        self._entidade_para_grupo = {}

    def pai_falhou(self, aba_pai, id_planilha) -> bool:
        chave = self._chave_entidade(aba_pai, id_planilha)
        if chave is None:
            return False
        return chave in self._entidade_para_grupo

    def grupo_do_pai(self, aba_pai, id_planilha) -> str | None:
        chave = self._chave_entidade(aba_pai, id_planilha)
        if chave is None:
            return None
        return self._entidade_para_grupo.get(chave)

    def registrar_falha_linha(
        self,
        aba,
        numero_linha,
        campo,
        valor,
        codigo,
        mensagem,
        id_planilha=None,
    ) -> ErroImportacaoDTO:
        if self._id_preenchido(id_planilha):
            grupo_id = id_grupo_entidade(aba, id_planilha)
            tipo = TIPO_GRUPO_FALHA_ENTIDADE
        else:
            grupo_id = id_grupo_linha(aba, numero_linha)
            tipo = TIPO_GRUPO_LINHA

        erro = ErroImportacaoDTO(
            aba=aba,
            numero_linha=numero_linha,
            campo=campo,
            valor=valor,
            codigo=codigo,
            mensagem=mensagem,
            grupo_id=grupo_id,
            papel=PAPEL_ERRO_CAUSA,
        )
        self._erros.append(erro)
        grupo = self._garantir_grupo(
            grupo_id,
            tipo,
            aba_entidade=aba,
            id_planilha=id_planilha,
        )
        grupo['causa_erro'] = erro
        if self._id_preenchido(id_planilha):
            self._vincular_entidade(aba, id_planilha, grupo_id)
        return erro

    def registrar_impacto(
        self,
        aba,
        numero_linha,
        campo,
        valor,
        codigo,
        mensagem,
        grupo_id,
        id_planilha=None,
    ) -> ErroImportacaoDTO:
        erro = ErroImportacaoDTO(
            aba=aba,
            numero_linha=numero_linha,
            campo=campo,
            valor=valor,
            codigo=codigo,
            mensagem=mensagem,
            grupo_id=grupo_id,
            papel=PAPEL_ERRO_IMPACTO,
        )
        self._erros.append(erro)
        grupo = self._grupos.get(grupo_id)
        if grupo is not None:
            grupo['impactos'].append(erro)
        if self._id_preenchido(id_planilha):
            self._vincular_entidade(aba, id_planilha, grupo_id)
        return erro

    def registrar_referencia_inexistente(
        self,
        aba,
        numero_linha,
        campo,
        valor,
        codigo,
        aba_referencia,
        id_referencia,
        id_planilha=None,
        mensagem=None,
    ) -> ErroImportacaoDTO:
        if not self._id_preenchido(id_referencia):
            return self.registrar_falha_linha(
                aba=aba,
                numero_linha=numero_linha,
                campo=campo,
                valor=valor,
                codigo=codigo,
                mensagem=mensagem or f'Referência de {aba_referencia} não informada.',
                id_planilha=id_planilha,
            )
        grupo_id = id_grupo_referencia(aba_referencia, id_referencia)
        id_normalizado = normalizar_id_referencia(id_referencia)
        self._garantir_grupo(
            grupo_id,
            TIPO_GRUPO_REFERENCIA_INEXISTENTE,
            aba_entidade=aba_referencia,
            id_planilha=id_referencia,
            mensagem_sintetica=(
                f'Referência "{aba_referencia} {id_normalizado}" não encontrada.'
            ),
        )
        if mensagem is None:
            mensagem = (
                f'Não importado: {aba_referencia} {id_normalizado} não foi encontrado '
                'na planilha nem no sistema.'
            )
        return self.registrar_impacto(
            aba=aba,
            numero_linha=numero_linha,
            campo=campo,
            valor=valor,
            codigo=codigo,
            mensagem=mensagem,
            grupo_id=grupo_id,
            id_planilha=id_planilha,
        )

    def primeira_dependencia_falha(self, aba, linha) -> dict | None:
        for dependencia in DEPENDENCIAS_DE_LINHA.get(aba, []):
            id_pai = getattr(linha, dependencia['attr'], None)
            if dependencia.get('opcional') and not self._id_preenchido(id_pai):
                continue
            if not self._id_preenchido(id_pai):
                continue
            if self.pai_falhou(dependencia['aba_pai'], id_pai):
                return {
                    'campo': dependencia['campo'],
                    'aba_pai': dependencia['aba_pai'],
                    'id_pai': id_pai,
                    'grupo_id': self.grupo_do_pai(dependencia['aba_pai'], id_pai),
                }
        return None

    def registrar_se_pais_falharam(self, aba, linha, codigo) -> bool:
        dependencia = self.primeira_dependencia_falha(aba, linha)
        if not dependencia:
            return False
        grupo_id = dependencia['grupo_id']
        mensagem = self._mensagem_impacto_pai(
            aba_pai=dependencia['aba_pai'],
            id_pai=dependencia['id_pai'],
            grupo_id=grupo_id,
        )
        self.registrar_impacto(
            aba=aba,
            numero_linha=linha.numero_linha,
            campo=dependencia['campo'],
            valor=dependencia['id_pai'],
            codigo=codigo,
            mensagem=mensagem,
            grupo_id=grupo_id,
            id_planilha=id_planilha_da_linha(aba, linha),
        )
        return True

    @property
    def erros(self) -> list[ErroImportacaoDTO]:
        causas = [erro for erro in self._erros if erro.papel == PAPEL_ERRO_CAUSA]
        impactos = [erro for erro in self._erros if erro.papel != PAPEL_ERRO_CAUSA]
        return causas + impactos

    def construir_grupos(self, estrutura=None) -> list[GrupoErroImportacaoDTO]:
        estrutura = estrutura if estrutura is not None else self._estrutura
        grupos = []
        for grupo_id in self._grupos_ordem:
            info = self._grupos[grupo_id]
            causa_erro = info.get('causa_erro')
            impactos_erros = info.get('impactos') or []
            tipo = info['tipo']
            aba_entidade = info.get('aba_entidade') or ''
            id_planilha = info.get('id_planilha')

            if causa_erro is not None:
                causa = CausaErroImportacaoDTO(
                    aba=causa_erro.aba,
                    id_planilha=id_planilha if self._id_preenchido(id_planilha) else None,
                    numero_linha=causa_erro.numero_linha,
                    rotulo=self._rotulo(estrutura, aba_entidade or causa_erro.aba, id_planilha),
                    campo=causa_erro.campo,
                    valor=causa_erro.valor,
                    codigo=causa_erro.codigo,
                    mensagem=causa_erro.mensagem,
                )
                titulo = causa_erro.mensagem
            elif tipo == TIPO_GRUPO_REFERENCIA_INEXISTENTE:
                mensagem = info.get('mensagem_sintetica') or (
                    f'Referência "{aba_entidade} {normalizar_id_referencia(id_planilha)}" não encontrada.'
                )
                causa = CausaErroImportacaoDTO(
                    aba=aba_entidade,
                    id_planilha=id_planilha,
                    numero_linha=0,
                    rotulo=self._rotulo(estrutura, aba_entidade, id_planilha),
                    campo='',
                    valor=id_planilha,
                    codigo=CODIGO_ERRO_REFERENCIA_NAO_ENCONTRADA,
                    mensagem=mensagem,
                )
                titulo = mensagem
            else:
                causa = None
                titulo = grupo_id

            impactos_por_aba = {}
            impactos = []
            for impacto in impactos_erros:
                impactos_por_aba[impacto.aba] = impactos_por_aba.get(impacto.aba, 0) + 1
                impactos.append(
                    ImpactoErroImportacaoDTO(
                        aba=impacto.aba,
                        numero_linha=impacto.numero_linha,
                        campo=impacto.campo,
                        valor=impacto.valor,
                        codigo=impacto.codigo,
                        mensagem=impacto.mensagem,
                    )
                )
            grupos.append(
                GrupoErroImportacaoDTO(
                    id=grupo_id,
                    tipo=tipo,
                    titulo=titulo,
                    causa=causa,
                    total_impactos=len(impactos),
                    impactos_por_aba=impactos_por_aba,
                    impactos=impactos,
                )
            )
        return grupos

    def _mensagem_impacto_pai(self, aba_pai, id_pai, grupo_id) -> str:
        grupo = self._grupos.get(grupo_id) or {}
        causa_erro = grupo.get('causa_erro')
        aba_raiz = grupo.get('aba_entidade') or aba_pai
        id_raiz = grupo.get('id_planilha')
        if not self._id_preenchido(id_raiz):
            id_raiz = id_pai
        id_normalizado = normalizar_id_referencia(id_raiz)
        if causa_erro is not None:
            return (
                f'Não importado: depende de {aba_raiz} {id_normalizado} '
                f'(linha {causa_erro.numero_linha}), que falhou: {causa_erro.mensagem}'
            )
        mensagem_sintetica = grupo.get('mensagem_sintetica')
        if mensagem_sintetica:
            return (
                f'Não importado: depende de {aba_raiz} {id_normalizado}, '
                f'que falhou: {mensagem_sintetica}'
            )
        return f'Não importado: depende de {aba_raiz} {id_normalizado}, que falhou.'

    def _rotulo(self, estrutura, aba, id_planilha) -> str:
        id_normalizado = normalizar_id_referencia(id_planilha)
        if not id_normalizado:
            return aba or ''
        linha = self._encontrar_linha(estrutura, aba, id_planilha)
        if linha is None:
            return f'{aba} {id_normalizado}'
        if aba == ABA_USUARIO:
            nome = (linha.nome or '').strip() or 'Usuário'
            cpf = linha.cpf or ''
            return f'{nome} (CPF {cpf})' if cpf else nome
        if aba == ABA_CURSO:
            return linha.codigo_curso or linha.nome or f'Curso {id_normalizado}'
        if aba == ABA_SETOR:
            return linha.sigla or linha.nome or f'Setor {id_normalizado}'
        if aba == ABA_CARGO:
            return linha.nome or f'Cargo {id_normalizado}'
        if aba == ABA_FUNCAO:
            return linha.papel_funcao or f'Funcao {id_normalizado}'
        if aba == ABA_EMPRESA_INSTITUICAO:
            return linha.nome or f'Empresa {id_normalizado}'
        if aba == ABA_ALUNO:
            return f'Aluno {id_normalizado}'
        return f'{aba} {id_normalizado}'

    def _encontrar_linha(self, estrutura, aba, id_planilha):
        if estrutura is None or not self._id_preenchido(id_planilha):
            return None
        colecao_attr = COLECAO_POR_ABA.get(aba)
        id_attr = ATTR_ID_PLANILHA_POR_ABA.get(aba)
        if not colecao_attr or not id_attr:
            return None
        alvo = normalizar_id_referencia(id_planilha)
        for linha in getattr(estrutura, colecao_attr, []) or []:
            if normalizar_id_referencia(getattr(linha, id_attr, None)) == alvo:
                return linha
        return None

    def _garantir_grupo(
        self,
        grupo_id,
        tipo,
        aba_entidade='',
        id_planilha=None,
        mensagem_sintetica='',
    ):
        grupo = self._grupos.get(grupo_id)
        if grupo is None:
            grupo = {
                'tipo': tipo,
                'aba_entidade': aba_entidade,
                'id_planilha': id_planilha,
                'causa_erro': None,
                'impactos': [],
                'mensagem_sintetica': mensagem_sintetica,
            }
            self._grupos[grupo_id] = grupo
            self._grupos_ordem.append(grupo_id)
            return grupo
        if aba_entidade and not grupo.get('aba_entidade'):
            grupo['aba_entidade'] = aba_entidade
        if self._id_preenchido(id_planilha) and not self._id_preenchido(grupo.get('id_planilha')):
            grupo['id_planilha'] = id_planilha
        if mensagem_sintetica and not grupo.get('mensagem_sintetica'):
            grupo['mensagem_sintetica'] = mensagem_sintetica
        return grupo

    def _vincular_entidade(self, aba, id_planilha, grupo_id):
        chave = self._chave_entidade(aba, id_planilha)
        if chave is None:
            return
        self._entidade_para_grupo[chave] = grupo_id

    def _chave_entidade(self, aba, id_planilha):
        if not aba or not self._id_preenchido(id_planilha):
            return None
        return (aba, normalizar_id_referencia(id_planilha))

    @staticmethod
    def _id_preenchido(id_planilha) -> bool:
        if id_planilha is None:
            return False
        if isinstance(id_planilha, str) and not id_planilha.strip():
            return False
        return True
