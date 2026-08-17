'''
Descritor de arquivo anexado no S3.

Cada app declara instâncias em ``constantes.py``. Este módulo não deve ser
reexportado pelo ``__init__.py`` do pacote ``storage``.
'''
from collections.abc import Iterator
from dataclasses import dataclass

from AppCore.core.exceptions.exceptions import NotFoundException

from . import s3


@dataclass(frozen=True)
class AnexoS3:
    '''
    Identifica um arquivo de uma entidade no bucket e nas rotas de proxy.

    ``caminho_fallback`` usa ``{id}`` como placeholder do pk
    (ex.: ``/cortex/identidade/usuarios/{id}/foto-secundaria/``).
    '''

    prefixo: str
    nome_url: str
    caminho_fallback: str

    def _chave_do_prefixo(self, valor: str | None) -> str | None:
        '''
        Normaliza a chave e aceita somente objetos sob ``self.prefixo``.

        O GET do proxy da API é anônimo; este filtro no descritor impede que
        uma chave arbitrária no banco vire leitura de qualquer objeto do bucket.
        '''
        chave = s3.normalizar_chave_s3(valor, prefixo=self.prefixo)
        if not chave or not chave.startswith(f'{self.prefixo}/'):
            return None
        return chave

    def url_proxy(self, objeto_id: int, chave: str | None, request=None) -> str | None:
        '''Monta a URL pública do proxy da API para o objeto no S3.'''
        return s3.montar_url_proxy_arquivo(
            objeto_id,
            chave,
            self.nome_url,
            request,
            caminho_fallback=self.caminho_fallback.format(id=objeto_id),
        )

    def enviar(self, objeto_id: int, arquivo, **kwargs) -> str:
        '''Envia o arquivo ao prefixo deste anexo e devolve a chave S3.'''
        return s3.enviar_arquivo_s3(self.prefixo, objeto_id, arquivo, **kwargs)

    def remover(self, chave: str | None) -> None:
        '''Remove o objeto no S3 de forma best-effort, se houver chave no prefixo.'''
        chave_valida = self._chave_do_prefixo(chave)
        if not chave_valida:
            return
        s3.remover_objeto_s3(chave_valida, prefixo=self.prefixo)

    def chave_normalizada(self, valor: str | None) -> str | None:
        '''Normaliza URL ou chave pura e devolve a chave apenas se estiver no prefixo.'''
        return self._chave_do_prefixo(valor)

    def iterar(self, chave: str, **kwargs) -> tuple[Iterator[bytes], str]:
        '''Obtém o stream e o content-type do objeto no S3, somente no prefixo.'''
        chave_valida = self._chave_do_prefixo(chave)
        if not chave_valida:
            raise NotFoundException('Objeto não encontrado.')
        return s3.iterar_objeto_s3(chave_valida, **kwargs)
