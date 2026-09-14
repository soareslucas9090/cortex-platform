from django.apps import apps

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class PermissaoFuncaoTransporteHelpers(ModelInstanceHelpers):

    def obter_ids_funcoes_ativas_do_usuario(self, usuario):
        SetorVinculo = apps.get_model('vinculos', 'SetorVinculo')
        return (
            SetorVinculo.objects.filter(
                usuario=usuario,
                setor__ativo=True,
                funcao__isnull=False,
                funcao__ativo=True,
            )
            .values_list('funcao_id', flat=True)
            .distinct()
        )

    def funcao_confere(self, usuario) -> bool:
        from .models import PermissaoFuncaoTransporte

        return PermissaoFuncaoTransporte.objects.filter(
            funcao_id__in=self.obter_ids_funcoes_ativas_do_usuario(usuario),
            conferir=True,
        ).exists()

    def existe_para_funcao(self, funcao_id) -> bool:
        from .models import PermissaoFuncaoTransporte

        return PermissaoFuncaoTransporte.objects.filter(funcao_id=funcao_id).exists()

    def usuario_confere(self, usuario) -> bool:
        from .models import PermissaoUsuarioTransporte

        if PermissaoUsuarioTransporte.objects.filter(usuario=usuario, conferir=True).exists():
            return True
        return self.funcao_confere(usuario)

    def funcao_visualiza_relatorio_alunos(self, usuario) -> bool:
        from Organizacional.funcoes.choices import CategoriaFuncao

        from .models import PermissaoFuncaoTransporte

        SetorVinculo = apps.get_model('vinculos', 'SetorVinculo')
        categorias_gestoras = (
            CategoriaFuncao.DIRETOR,
            CategoriaFuncao.COORDENADOR,
            CategoriaFuncao.CHEFE,
        )
        if SetorVinculo.objects.filter(
            usuario=usuario,
            setor__ativo=True,
            funcao__ativo=True,
            funcao__categoria__in=categorias_gestoras,
        ).exists():
            return True

        return PermissaoFuncaoTransporte.objects.filter(
            funcao_id__in=self.obter_ids_funcoes_ativas_do_usuario(usuario),
            visualizar_relatorio_alunos=True,
        ).exists()

    def usuario_visualiza_relatorio_alunos(self, usuario) -> bool:
        from .models import PermissaoUsuarioTransporte

        if PermissaoUsuarioTransporte.objects.filter(
            usuario=usuario,
            visualizar_relatorio_alunos=True,
        ).exists():
            return True
        return self.funcao_visualiza_relatorio_alunos(usuario)


class PermissaoUsuarioTransporteHelpers(ModelInstanceHelpers):

    def existe_para_usuario(self, usuario_id) -> bool:
        from .models import PermissaoUsuarioTransporte

        return PermissaoUsuarioTransporte.objects.filter(usuario_id=usuario_id).exists()

    def obter_capacidades(self) -> dict:
        permissao = self.object_instance
        return {
            'conferir': bool(permissao.conferir),
            'visualizar_relatorio_alunos': bool(
                permissao.visualizar_relatorio_alunos,
            ),
        }
