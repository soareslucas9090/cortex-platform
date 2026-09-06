import AppCore.core.business.business_mixin
import AppCore.core.helpers.helpers_mixin
import AppCore.core.rules.rules_mixin
import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('alunos', '0001_initial'),
        ('execucoes_rotas', '0002_conferencia'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalEntradaSemTicket',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('cpf', models.CharField(max_length=14, verbose_name='CPF')),
                ('observacao', models.TextField(blank=True, default='', verbose_name='Observação')),
                ('data_hora_entrada', models.DateTimeField(verbose_name='Data e hora da entrada')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('aluno', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='alunos.aluno', verbose_name='Aluno')),
                ('execucao_rota', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='execucoes_rotas.execucaorota', verbose_name='Execução da rota')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Entrada sem ticket',
                'verbose_name_plural': 'historical Entradas sem ticket',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='EntradaSemTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cpf', models.CharField(max_length=14, verbose_name='CPF')),
                ('observacao', models.TextField(blank=True, default='', verbose_name='Observação')),
                ('data_hora_entrada', models.DateTimeField(verbose_name='Data e hora da entrada')),
                ('aluno', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entradas_sem_ticket', to='alunos.aluno', verbose_name='Aluno')),
                ('execucao_rota', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entradas_sem_ticket', to='execucoes_rotas.execucaorota', verbose_name='Execução da rota')),
            ],
            options={
                'verbose_name': 'Entrada sem ticket',
                'verbose_name_plural': 'Entradas sem ticket',
                'ordering': ['data_hora_entrada'],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('execucao_rota', 'aluno'),
                        name='entrada_sem_ticket_unica_aluno_execucao',
                    ),
                ],
            },
            bases=(AppCore.core.helpers.helpers_mixin.ModelHelperMixin, AppCore.core.business.business_mixin.ModelBusinessMixin, AppCore.core.rules.rules_mixin.ModelRulesMixin, models.Model),
        ),
    ]
