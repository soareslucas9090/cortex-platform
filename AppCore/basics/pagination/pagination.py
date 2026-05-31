from rest_framework.pagination import PageNumberPagination


class PaginacaoCustomizada(PageNumberPagination):
    """
    Classe de paginação customizada que permite controle dinâmico do tamanho da página.
    
    - Tamanho padrão: 10 itens por página
    - Query param 'paginacao': permite definir o tamanho da página (entre 1 e 100)
    - Valores menores que 1 são ajustados para 1
    - Valores maiores que 100 são ajustados para 100
    
    Exemplo de uso:
        /cortex/api/usuarios/?paginacao=20  → Retorna 20 itens por página
        /cortex/api/usuarios/?paginacao=150 → Retorna 100 itens por página (máximo)
        /cortex/api/usuarios/?paginacao=0   → Retorna 1 item por página (mínimo)
    """
    page_size = 10
    page_size_query_param = 'paginacao'
    max_page_size = 100

    def get_page_size(self, request):
        """
        Retorna o tamanho da página baseado no query param 'paginacao'.
        
        Garante que o valor esteja entre 1 e 100.
        """
        if self.page_size_query_param:
            try:
                page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
                
                # Garante que o valor esteja entre 1 e 100
                if page_size < 1:
                    return 1
                elif page_size > 100:
                    return 100
                
                return page_size
            except (ValueError, TypeError):
                pass
        
        return self.page_size
