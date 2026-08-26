# Generated manually for Infraestrutura.importacoes

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportacaoLote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('arquivo', models.FileField(upload_to='importacoes/infraestrutura/%Y/%m/%d/', verbose_name='Arquivo de Importação')),
                ('status', models.CharField(choices=[('EM_ANDAMENTO', 'Em Andamento'), ('CONCLUIDA', 'Concluída'), ('ERRO', 'Erro')], default='EM_ANDAMENTO', max_length=20, verbose_name='Status')),
                ('total_linhas', models.IntegerField(default=0, verbose_name='Total de Linhas')),
                ('linhas_processadas', models.IntegerField(default=0, verbose_name='Linhas Processadas')),
                ('resultado_json', models.JSONField(blank=True, null=True, verbose_name='Resultado/Erros')),
            ],
            options={
                'verbose_name': 'Importação de Lote de Infraestrutura',
                'verbose_name_plural': 'Importações de Lote de Infraestrutura',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalImportacaoLote',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('arquivo', models.TextField(max_length=100, verbose_name='Arquivo de Importação')),
                ('status', models.CharField(choices=[('EM_ANDAMENTO', 'Em Andamento'), ('CONCLUIDA', 'Concluída'), ('ERRO', 'Erro')], default='EM_ANDAMENTO', max_length=20, verbose_name='Status')),
                ('total_linhas', models.IntegerField(default=0, verbose_name='Total de Linhas')),
                ('linhas_processadas', models.IntegerField(default=0, verbose_name='Linhas Processadas')),
                ('resultado_json', models.JSONField(blank=True, null=True, verbose_name='Resultado/Erros')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Importação de Lote de Infraestrutura',
                'verbose_name_plural': 'historical Importações de Lote de Infraestrutura',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.RunSQL(
            sql="SET LOCAL lock_timeout = '2s';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddConstraint(
            model_name='importacaolote',
            constraint=models.UniqueConstraint(
                condition=models.Q(('status', 'EM_ANDAMENTO')),
                fields=('status',),
                name='importacoes_infraestrutura_lote_unico_em_andamento',
            ),
        ),
    ]
