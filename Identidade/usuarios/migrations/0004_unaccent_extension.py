from django.db import migrations
from django.contrib.postgres.operations import UnaccentExtension

class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_alter_historicalusuario_cpf_alter_usuario_cpf'),
    ]

    operations = [
        UnaccentExtension(),
    ]
