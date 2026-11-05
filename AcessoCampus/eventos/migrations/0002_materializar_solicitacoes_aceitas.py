import uuid
from datetime import time

from django.db import migrations


def materializar_solicitacoes_aceitas(apps, schema_editor):
    SolicitacaoAcesso = apps.get_model(
        "acesso_campus_solicitacoes",
        "SolicitacaoAcesso",
    )
    EventoAcesso = apps.get_model("acesso_campus_eventos", "EventoAcesso")
    grupos_turma = {}

    for solicitacao in SolicitacaoAcesso.objects.filter(status=2).iterator():
        if solicitacao.turma_origem and solicitacao.lote_id:
            chave = (solicitacao.lote_id, solicitacao.turma_origem)
            grupo_portaria_id = grupos_turma.setdefault(chave, uuid.uuid4())
        else:
            grupo_portaria_id = uuid.uuid4()
        EventoAcesso.objects.get_or_create(
            solicitacao_id=solicitacao.pk,
            defaults={
                "aluno_id": solicitacao.aluno_id,
                "grupo_portaria_id": grupo_portaria_id,
                "tipo": solicitacao.tipo,
                "data_acesso": solicitacao.data_acesso,
                "hora_prevista": solicitacao.hora_autorizada or time(8, 0),
                "turma_origem": solicitacao.turma_origem,
                "aluno_nome": solicitacao.aluno_nome,
                "curso_nome": solicitacao.curso_nome,
                "matricula": solicitacao.matricula,
            },
        )


def remover_eventos_materializados(apps, schema_editor):
    EventoAcesso = apps.get_model("acesso_campus_eventos", "EventoAcesso")
    EventoAcesso.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("acesso_campus_eventos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            materializar_solicitacoes_aceitas,
            reverse_code=remover_eventos_materializados,
        ),
    ]
