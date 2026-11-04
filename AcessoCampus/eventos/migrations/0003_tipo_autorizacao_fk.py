import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acesso_campus_eventos", "0002_materializar_solicitacoes_aceitas"),
        ("acesso_campus_solicitacoes", "0003_tipo_autorizacao_fk"),
        ("acesso_campus_tipos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicaleventoacesso",
            name="tipo",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="acesso_campus_tipos.tipoautorizacaoacesso",
                verbose_name="Tipo de movimento",
            ),
        ),
        migrations.AlterField(
            model_name="eventoacesso",
            name="tipo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="eventos_acesso",
                to="acesso_campus_tipos.tipoautorizacaoacesso",
                verbose_name="Tipo de movimento",
            ),
        ),
    ]
