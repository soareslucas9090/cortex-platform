from django.db import migrations


def inserir_cursos_raizes(apps, schema_editor):
    Curso = apps.get_model('cursos', 'Curso')

    cursos = [
        {"nome": "Formação Inicial em Agente de Inclusão Digital em Centros Públicos de Acesso à Internet - Campus Floriano", "codigo_curso": "14FAID", "ativo": True},
        {"nome": "Formação Inicial em Língua Brasileira de Sinais (Libras) - Básico - Campus Floriano", "codigo_curso": "14FLIB", "ativo": True},
        {"nome": "Formação Inicial em Inglês Básico - Campus Floriano", "codigo_curso": "14FINB", "ativo": True},
        {"nome": "Formação Inicial em Eletricista de Sistemas de Energias Renováveis - Campus Floriano", "codigo_curso": "14FSER", "ativo": True},
        {"nome": "Especialização em Desenvolvimento para Web", "codigo_curso": "S.52", "ativo": True},
        {"nome": "Especialização em Desporto Escolar e Desempenho Humano", "codigo_curso": "S.53", "ativo": True},
        {"nome": "Especialização em Ensino de Matemática no Ensino Médio", "codigo_curso": "S.55", "ativo": True},
        {"nome": "Especialização em Matemática", "codigo_curso": "S.54", "ativo": True},
        {"nome": "Especialização no Ensino de Ciências Biológicas", "codigo_curso": "14EECB", "ativo": True},
        {"nome": "Licenciatura em Ciências Biológicas / PARFOR - 2ª Licenciatura", "codigo_curso": "S.04", "ativo": True},
        {"nome": "Licenciatura em Ciências Biológicas - Floriano", "codigo_curso": "14LBIO", "ativo": True},
        {"nome": "Licenciatura em Ciências Biológicas / PARFOR - 1ª Licenciatura", "codigo_curso": "S.03", "ativo": True},
        {"nome": "Licenciatura em Matemática - Floriano", "codigo_curso": "14LMAT", "ativo": True},
        {"nome": "Licenciatura em Matemática / PARFOR - 2ª Licenciatura", "codigo_curso": "S.05", "ativo": True},
        {"nome": "Mestrado Profissional em Matemática / PROFMAT - Floriano", "codigo_curso": "14PMAT", "ativo": True},
        {"nome": "Técnico de Informática - Concomitante/Subsequente - Floriano", "codigo_curso": "14MINF", "ativo": True},
        {"nome": "Técnico de Segurança do Trabalho - EaD", "codigo_curso": "B.61", "ativo": True},
        {"nome": "Técnico de Serviços Jurídicos Subsequente - EaD", "codigo_curso": "B.62", "ativo": True},
        {"nome": "Técnico em Administração - EaD", "codigo_curso": "TEAD", "ativo": True},
        {"nome": "Técnico em Desenvolvimento de Sistemas - Concomitante/Subsequente - Floriano", "codigo_curso": "14MTDS", "ativo": True},
        {"nome": "Técnico em Edificações - Concomitante/Subsequente - Floriano", "codigo_curso": "14MEDF", "ativo": True},
        {"nome": "Técnico em Edificações - Integrado - Floriano", "codigo_curso": "14IEDF", "ativo": True},
        {"nome": "Técnico em Eletromecânica - Concomitante/Subsequente - Floriano", "codigo_curso": "14MELM", "ativo": True},
        {"nome": "Técnico em Eletromecânica - Integrado - Floriano", "codigo_curso": "14IELM", "ativo": True},
        {"nome": "Técnico em Informática - Integrado - Floriano", "codigo_curso": "14IINF", "ativo": True},
        {"nome": "Técnico em Informática para Internet - EaD", "codigo_curso": "IPINT", "ativo": True},
        {"nome": "Técnico em Logística - EaD", "codigo_curso": "LOGI", "ativo": True},
        {"nome": "Técnico em Meio Ambiente - EaD", "codigo_curso": "MEAB", "ativo": True},
        {"nome": "Técnico em Meio Ambiente - Integrado - Floriano", "codigo_curso": "14IAMB", "ativo": True},
        {"nome": "Técnico em Redes de Computadores", "codigo_curso": "B.67", "ativo": True},
        {"nome": "Técnico em Secretariado - EaD", "codigo_curso": "SECR", "ativo": True},
        {"nome": "Técnico em Serviços Públicos - EAD", "codigo_curso": "TPF", "ativo": True},
        {"nome": "Tecnologia em Análise e Desenvolvimento de Sistemas - Floriano", "codigo_curso": "14TADS", "ativo": True},
        {"nome": "Técnico em Meio Ambiente Integrado ao Ensino Médio - PROEJA", "codigo_curso": "14JAMB", "ativo": True},
        {"nome": "Formação Inicial em Músico de Banda", "codigo_curso": "14FMB", "ativo": True},
        {"nome": "Curso de Qualificação Profissional em Operador de Computador na Modalidade de Educação de Jovens e Adultos PROEJA-FIC-EPT", "codigo_curso": "14JOPC", "ativo": True},
        {"nome": "Técnico em Administração- Integrado - Floriano", "codigo_curso": "14IADM", "ativo": True},
        {"nome": "Bacharelado em Engenharia Civil - CAFLO", "codigo_curso": "14BECV", "ativo": True},
        {"nome": "Eletricista de Sistema de Energias Renováveis", "codigo_curso": "14ASER", "ativo": True},
        {"nome": "Preparatório para o Ensino Médio - PARTIU IF", "codigo_curso": "14PIFPI", "ativo": True},
        {"nome": "Formação Inicial em Redator de Textos Técnicos", "codigo_curso": "14FRT", "ativo": True},
    ]

    for curso_data in cursos:
        # Usa get_or_create com base na chave natural codigo_curso para garantir idempotência.
        # Os campos adicionais são definidos no defaults para não alterar os dados se o registro já existir.
        Curso.objects.get_or_create(
            codigo_curso=curso_data['codigo_curso'],
            defaults={
                'nome': curso_data['nome'],
                'turno': None,
                'ativo': curso_data['ativo'],
            }
        )


def remover_cursos_raizes(apps, schema_editor):
    Curso = apps.get_model('cursos', 'Curso')
    codigos = [
        "14FAID", "14FLIB", "14FINB", "14FSER", "S.52", "S.53", "S.55", "S.54", "14EECB",
        "S.04", "14LBIO", "S.03", "14LMAT", "S.05", "14PMAT", "14MINF", "B.61", "B.62",
        "TEAD", "14MTDS", "14MEDF", "14IEDF", "14MELM", "14IELM", "14IINF", "IPINT",
        "LOGI", "MEAB", "14IAMB", "B.67", "SECR", "TPF", "14TADS", "14JAMB", "14FMB",
        "14JOPC", "14IADM", "14BECV", "14ASER", "14PIFPI", "14FRT"
    ]
    Curso.objects.filter(codigo_curso__in=codigos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(inserir_cursos_raizes, reverse_code=remover_cursos_raizes),
    ]
