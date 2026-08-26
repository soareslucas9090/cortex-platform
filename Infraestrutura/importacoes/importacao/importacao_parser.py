from pathlib import Path

from .importacao_constants import (
    ABAS_OBRIGATORIAS_MINIMAS,
    ABA_BLOCO,
    ABA_RECURSO,
    ABA_SALA,
    ALIAS_CABECALHOS_IMPORTACAO,
    COLUNAS_ESPERADAS_POR_ABA,
    EXTENSOES_SUPORTADAS,
    TIPOS_RECURSO_VALIDOS,
)
from .importacao_dtos import (
    ArquivoImportacaoInfraestruturaDTO,
    LinhaBlocoImportacaoDTO,
    LinhaRecursoImportacaoDTO,
    LinhaSalaImportacaoDTO,
)
from .importacao_exceptions import (
    AbaObrigatoriaAusenteException,
    ArquivoImportacaoInvalidoException,
    ColunasObrigatoriasAusentesException,
)

try:
    from pyexcel_ods3 import get_data
except ImportError:  # pragma: no cover
    get_data = None


class ImportacaoInfraestruturaParser:
    """Parser da planilha .ods multiaba de importação em lote de infraestrutura."""

    def parse(self, arquivo) -> ArquivoImportacaoInfraestruturaDTO:
        self._validar_arquivo(arquivo)
        planilha = self._ler_planilha(arquivo)
        self._validar_abas_minimas(planilha)

        resultado = ArquivoImportacaoInfraestruturaDTO()

        if ABA_BLOCO in planilha:
            resultado.blocos = self._parse_blocos(planilha[ABA_BLOCO])

        if ABA_SALA in planilha:
            resultado.salas = self._parse_salas(planilha[ABA_SALA])

        if ABA_RECURSO in planilha:
            resultado.recursos = self._parse_recursos(planilha[ABA_RECURSO])

        return resultado

    def _validar_arquivo(self, arquivo):
        if not arquivo:
            raise ArquivoImportacaoInvalidoException('Arquivo de importação não enviado.')

        suffix = Path(arquivo.name).suffix.lower()
        if suffix not in EXTENSOES_SUPORTADAS:
            raise ArquivoImportacaoInvalidoException(
                f'Extensão "{suffix}" não suportada. Extensões permitidas: {", ".join(EXTENSOES_SUPORTADAS)}.'
            )

        if get_data is None:
            raise ArquivoImportacaoInvalidoException(
                'Biblioteca de leitura .ods não instalada. Instale pyexcel-ods3.'
            )

    def _ler_planilha(self, arquivo):
        try:
            arquivo.seek(0)
            dados = get_data(arquivo)
            return {str(nome).strip().lower(): conteudo for nome, conteudo in dados.items()}
        except Exception as exc:
            raise ArquivoImportacaoInvalidoException(
                f'Não foi possível ler o arquivo .ods: {exc}'
            ) from exc

    def _validar_abas_minimas(self, planilha):
        for aba in ABAS_OBRIGATORIAS_MINIMAS:
            if aba not in planilha:
                raise AbaObrigatoriaAusenteException(
                    f'A aba obrigatória "{aba}" não foi encontrada no arquivo.'
                )

    def _extrair_linhas(self, dados_aba, nome_aba):
        if not dados_aba:
            return []

        header_raw = dados_aba[0]
        header = [self._normalizar_cabecalho(valor) for valor in header_raw]

        colunas_esperadas = COLUNAS_ESPERADAS_POR_ABA.get(nome_aba, [])
        ausentes = [col for col in colunas_esperadas if col not in header]
        if ausentes:
            raise ColunasObrigatoriasAusentesException(
                f'A aba "{nome_aba}" não contém as colunas obrigatórias: {", ".join(ausentes)}.'
            )

        linhas = []
        for index, row in enumerate(dados_aba[1:], start=2):
            row_limpo = [self._limpar_valor(v) for v in row]

            item = {}
            for i, coluna in enumerate(header):
                if not coluna:
                    continue
                item[coluna] = row_limpo[i] if i < len(row_limpo) else None

            if self._linha_vazia([item.get(col) for col in colunas_esperadas]):
                continue

            item['numero_linha'] = index
            linhas.append(item)

        return linhas

    def _limpar_valor(self, valor):
        if isinstance(valor, str):
            v_strip = valor.strip()
            v_upper = v_strip.upper()
            if v_upper == 'NULL' or v_strip == '-' or v_strip == '':
                return None
            return v_strip
        return valor

    def _normalizar_cabecalho(self, valor):
        if valor is None:
            return ''

        texto = str(valor).strip()
        if '\n' in texto:
            texto = texto.split('\n')[0].strip()

        if ' (' in texto:
            texto = texto.split(' (')[0].strip()

        texto = texto.lower()
        return ALIAS_CABECALHOS_IMPORTACAO.get(texto, texto)

    def _linha_vazia(self, row):
        return all(valor is None for valor in row)

    def _parse_blocos(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, ABA_BLOCO)
        return [
            LinhaBlocoImportacaoDTO(
                numero_linha=linha['numero_linha'],
                bloco_id_planilha=self._to_int(linha.get('bloco_id')),
                nome=self._to_str(linha.get('nome')),
            )
            for linha in linhas
        ]

    def _parse_salas(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, ABA_SALA)
        return [
            LinhaSalaImportacaoDTO(
                numero_linha=linha['numero_linha'],
                sala_id_planilha=self._to_int(linha.get('sala_id')),
                bloco_id_planilha=self._to_int(linha.get('bloco_id')),
                nome=self._to_str(linha.get('nome')),
            )
            for linha in linhas
        ]

    def _parse_recursos(self, dados_aba):
        linhas = self._extrair_linhas(dados_aba, ABA_RECURSO)
        resultado = []
        for linha in linhas:
            tipo = self._to_str(linha.get('tipo')).lower()
            if tipo and tipo not in TIPOS_RECURSO_VALIDOS:
                raise ArquivoImportacaoInvalidoException(
                    f'Tipo de recurso inválido na linha {linha["numero_linha"]}: {tipo}.'
                )
            resultado.append(
                LinhaRecursoImportacaoDTO(
                    numero_linha=linha['numero_linha'],
                    sala_id_planilha=self._to_int(linha.get('sala_id')),
                    descricao=self._to_str(linha.get('descricao')),
                    codigo=self._to_str(linha.get('codigo')),
                    em_avaria=self._to_bool(linha.get('avaria'), default=False),
                    tipo=tipo,
                    foto_url=self._to_str(linha.get('foto')),
                )
            )
        return resultado

    def _to_str(self, valor):
        if valor is None:
            return ''
        return str(valor).strip()

    def _to_int(self, valor):
        if valor in (None, ''):
            return None
        return int(valor)

    def _to_bool(self, valor, default=False):
        if valor in (None, ''):
            return default

        if isinstance(valor, bool):
            return valor

        texto = str(valor).strip().lower()
        if texto in ('true', '1', 'sim', 's', 'yes'):
            return True
        if texto in ('false', '0', 'nao', 'não', 'n', 'no'):
            return False

        return default
