from django.db import migrations


def popular_categoria_funcoes(apps, schema_editor):
    Funcao = apps.get_model('funcoes', 'Funcao')

    for funcao in Funcao.objects.all():
        papel = funcao.papel_funcao
        if papel.startswith('Diretor'):
            categoria = 'diretor'
        elif papel.startswith('Chefe'):
            categoria = 'chefe'
        else:
            categoria = 'coordenador'
        funcao.categoria = categoria
        funcao.save(update_fields=['categoria'])


class Migration(migrations.Migration):

    dependencies = [
        ('funcoes', '0003_funcao_categoria'),
    ]

    operations = [
        migrations.RunPython(popular_categoria_funcoes, migrations.RunPython.noop),
    ]
