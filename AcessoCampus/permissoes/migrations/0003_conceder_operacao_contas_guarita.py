from django.db import migrations


def conceder_operacao_contas_guarita(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Permissao = apps.get_model(
        'acesso_campus_permissoes',
        'PermissaoUsuarioAcessoCampus',
    )

    contas_guarita = Usuario.objects.filter(
        usuario_coletivo=True,
        tipo_conta_coletiva='guarita',
        ativo=True,
    ).values_list('pk', flat=True)

    for usuario_id in contas_guarita.iterator():
        permissao, _ = Permissao.objects.get_or_create(usuario_id=usuario_id)
        if not permissao.operar_portaria:
            permissao.operar_portaria = True
            permissao.save(update_fields=['operar_portaria', 'updated_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('acesso_campus_permissoes', '0002_conceder_analise_cinco_papeis'),
        ('usuarios', '0003_alter_usuario_tipo_conta_coletiva'),
    ]

    operations = [
        migrations.RunPython(
            conceder_operacao_contas_guarita,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
