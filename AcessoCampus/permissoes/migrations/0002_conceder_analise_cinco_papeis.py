from django.db import migrations

PAPEIS_ESCOPO_GLOBAL = (
    'Diretor(a) de Ensino',
    'Chefe de Departamento de Ensino Técnico',
    'Chefe de Departamento de Apoio ao Ensino',
    'Coordenador(a) de Disciplina',
    'Coordenador(a) das Áreas de Natureza, Humanas e Letras',
)


def conceder_analise(apps, schema_editor):
    Funcao = apps.get_model('funcoes', 'Funcao')
    Permissao = apps.get_model('acesso_campus_permissoes', 'PermissaoFuncaoAcessoCampus')
    for funcao in Funcao.objects.filter(papel_funcao__in=PAPEIS_ESCOPO_GLOBAL):
        Permissao.objects.update_or_create(
            funcao_id=funcao.pk,
            defaults={'analisar_solicitacoes': True},
        )


def revogar_analise(apps, schema_editor):
    Permissao = apps.get_model('acesso_campus_permissoes', 'PermissaoFuncaoAcessoCampus')
    Funcao = apps.get_model('funcoes', 'Funcao')
    funcao_ids = Funcao.objects.filter(papel_funcao__in=PAPEIS_ESCOPO_GLOBAL).values_list('pk', flat=True)
    Permissao.objects.filter(funcao_id__in=funcao_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('acesso_campus_permissoes', '0001_initial'),
        ('funcoes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(conceder_analise, reverse_code=revogar_analise),
    ]
