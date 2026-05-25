from django.db import migrations


def inserir_cargos_raizes(apps, schema_editor):
    Cargo = apps.get_model('cargos', 'Cargo')

    cargos = [
        {"nome": "PROF ENS BAS TEC TECNOLOGICO-SUBSTITUTO", "ativo": True},
        {"nome": "ASSISTENTE EM ADMINISTRACAO", "ativo": True},
        {"nome": "ASSISTENTE DE ALUNO", "ativo": True},
        {"nome": "ADMINISTRADOR", "ativo": True},
        {"nome": "TEC DE TECNOLOGIA DA INFORMACAO", "ativo": True},
        {"nome": "PROFESSOR ENS BASICO TECN TECNOLOGICO", "ativo": True},
        {"nome": "ENGENHEIRO", "ativo": True},
        {"nome": "BIBLIOTECARIO-DOCUMENTALISTA", "ativo": True},
        {"nome": "VIGILANTE", "ativo": True},
        {"nome": "TECNICO EM AUDIOVISUAL", "ativo": True},
        {"nome": "CONTADOR", "ativo": True},
        {"nome": "AUXILIAR DE BIBLIOTECA", "ativo": True},
        {"nome": "AUX EM ADMINISTRACAO", "ativo": True},
        {"nome": "ENFERMEIRO", "ativo": True},
        {"nome": "TECNICO EM ELETROTECNICA", "ativo": True},
        {"nome": "TECNICO DE LABORATORIO", "ativo": True},
        {"nome": "PSICOLOGO", "ativo": True},
        {"nome": "TECNICO EM ARQUIVO", "ativo": True},
        {"nome": "ASSISTENTE SOCIAL", "ativo": True},
        {"nome": "TECNICO EM ASSUNTOS EDUCACIONAIS", "ativo": True},
        {"nome": "ODONTOLOGO - 40 HORAS", "ativo": True},
        {"nome": "SECRETARIO EXECUTIVO", "ativo": True},
        {"nome": "PEDAGOGO", "ativo": True},
        {"nome": "ASSISTENTE DE LABORATORIO", "ativo": True},
        {"nome": "NUTRICIONISTA-HABILITACAO", "ativo": True},
        {"nome": "MEDICO - PCCTAE", "ativo": True},
        {"nome": "TECNICO EM ENFERMAGEM", "ativo": True},
        {"nome": "TECNICO EM SECRETARIADO", "ativo": True},
        {"nome": "ANALISTA DE TEC DA INFORMACAO", "ativo": True},
    ]

    for cargo_data in cargos:
        # Usa get_or_create com base no nome para garantir a idempotência.
        Cargo.objects.get_or_create(
            nome=cargo_data['nome'],
            defaults={
                'ativo': cargo_data['ativo'],
            }
        )


def remover_cargos_raizes(apps, schema_editor):
    Cargo = apps.get_model('cargos', 'Cargo')
    nomes = [
        "PROF ENS BAS TEC TECNOLOGICO-SUBSTITUTO",
        "ASSISTENTE EM ADMINISTRACAO",
        "ASSISTENTE DE ALUNO",
        "ADMINISTRADOR",
        "TEC DE TECNOLOGIA DA INFORMACAO",
        "PROFESSOR ENS BASICO TECN TECNOLOGICO",
        "ENGENHEIRO",
        "BIBLIOTECARIO-DOCUMENTALISTA",
        "VIGILANTE",
        "TECNICO EM AUDIOVISUAL",
        "CONTADOR",
        "AUXILIAR DE BIBLIOTECA",
        "AUX EM ADMINISTRACAO",
        "ENFERMEIRO",
        "TECNICO EM ELETROTECNICA",
        "TECNICO DE LABORATORIO",
        "PSICOLOGO",
        "TECNICO EM ARQUIVO",
        "ASSISTENTE SOCIAL",
        "TECNICO EM ASSUNTOS EDUCACIONAIS",
        "ODONTOLOGO - 40 HORAS",
        "SECRETARIO EXECUTIVO",
        "PEDAGOGO",
        "ASSISTENTE DE LABORATORIO",
        "NUTRICIONISTA-HABILITACAO",
        "MEDICO - PCCTAE",
        "TECNICO EM ENFERMAGEM",
        "TECNICO EM SECRETARIADO",
        "ANALISTA DE TEC DA INFORMACAO",
    ]
    Cargo.objects.filter(nome__in=nomes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cargos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(inserir_cargos_raizes, reverse_code=remover_cargos_raizes),
    ]
