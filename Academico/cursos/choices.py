from django.db import models


class NivelEnsino(models.IntegerChoices):
    ENSINO_MEDIO = 1, 'Ensino Médio'
    TECNICO = 2, 'Técnico'
    SUPERIOR = 3, 'Superior'
    POS_GRADUACAO = 4, 'Pós-graduação'
    FORMACAO_PROFISSIONAL = 5, 'Formação profissional'
    MESTRADO = 6, 'Mestrado'
    PREPARATORIO_VESTIBULAR = 7, 'Preparatório vestibular'


class Modalidade(models.IntegerChoices):
    FIC = 1, 'FIC'
    QUALIFICACAO_PROFISSIONAL = 2, 'Qualificação Profissional'
    CURSO_LIVRE = 3, 'Curso Livre'
    TECNICO_INTEGRADO = 4, 'Técnico Integrado'
    TECNICO_INTEGRADO_EJA = 5, 'Técnico Integrado EJA'
    TECNICO_SUBSEQUENTE = 6, 'Técnico Subsequente'
    TECNICO_SUBSEQUENTE_CONCOMITANTE = 7, 'Técnico Subsequente/Concomitante'
    TECNICO_SUBSEQUENTE_CONCOMITANTE_EAD = 8, 'Técnico Subsequente/Concomitante/EaD'
    LICENCIATURA = 9, 'Licenciatura'
    BACHARELADO = 10, 'Bacharelado'
    TECNOLOGIA = 11, 'Tecnologia'
    ESPECIALIZACAO = 12, 'Especialização'
    MESTRADO = 13, 'Mestrado'
