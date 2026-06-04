"""
Helpers Layer - Camada de Funções Utilitárias

Esta camada é responsável por:
- Queries customizadas e otimizadas
- Funções auxiliares reutilizáveis
- Operações de busca e filtragem
- Formatações e transformações de dados
- Utilitários que não se encaixam em Business ou Rules

Helpers devem ser:
- Funções puras quando possível
- Reutilizáveis em diferentes contextos
- Sem efeitos colaterais desnecessários
- Bem documentadas e testáveis
"""

class UserModelPermission:
    def __init__(self, object_instance=None):
        self.object_instance = object_instance

    def compilar_permissoes(self):
        permissoes = {}
        for attr_name in dir(self):
            if attr_name.startswith("permissoes_") and attr_name != "permissoes_":
                metodo = getattr(self, attr_name)
                if callable(metodo):
                    resultado = metodo()
                    if isinstance(resultado, dict):
                        permissoes.update(resultado)
        return permissoes
