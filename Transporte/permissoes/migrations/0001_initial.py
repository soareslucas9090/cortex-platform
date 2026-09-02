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
        ('funcoes', '0004_popular_categoria_funcoes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalPermissaoFuncaoTransporte',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('conferir', models.BooleanField(default=False, verbose_name='Conferir')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('funcao', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='funcoes.funcao', verbose_name='Função')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Permissão de Transporte por Função',
                'verbose_name_plural': 'historical Permissões de Transporte por Função',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='PermissaoFuncaoTransporte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('conferir', models.BooleanField(default=False, verbose_name='Conferir')),
                ('funcao', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='permissao_transporte', to='funcoes.funcao', verbose_name='Função')),
            ],
            options={
                'verbose_name': 'Permissão de Transporte por Função',
                'verbose_name_plural': 'Permissões de Transporte por Função',
                'ordering': ['funcao__papel_funcao'],
            },
            bases=(AppCore.core.helpers.helpers_mixin.ModelHelperMixin, AppCore.core.business.business_mixin.ModelBusinessMixin, AppCore.core.rules.rules_mixin.ModelRulesMixin, models.Model),
        ),
    ]
