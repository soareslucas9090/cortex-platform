from datetime import time, timedelta

from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from Academico.alunos.models import Aluno
from Identidade.usuarios.models import TipoDeficiencia, Usuario
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.percursos.models import Percurso
from Transporte.rotas.choices import DiaSemana
from Transporte.rotas.models import Rota


# TODO | feat/tickets-transporte | Lucas Soares | 01-09-2026: Adequar os testes para o padrão do projeto

DIAS_POR_WEEKDAY = {
    0: DiaSemana.SEGUNDA,
    1: DiaSemana.TERCA,
    2: DiaSemana.QUARTA,
    3: DiaSemana.QUINTA,
    4: DiaSemana.SEXTA,
    5: DiaSemana.SABADO,
    6: DiaSemana.DOMINGO,
}


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_usuario(cpf, nome='Usuário', admin=False, deficiencia=None):
    dados = {'cpf': cpf, 'password': 'Senha@123', 'nome': nome, 'deficiencia': deficiencia}
    if admin:
        return Usuario.objects.create_superuser(**dados)
    return Usuario.objects.create_user(**dados)


def criar_aluno(cpf, nome='Aluno', deficiencia=None, **kwargs):
    usuario = criar_usuario(cpf, nome=nome, deficiencia=deficiencia)
    return Aluno.objects.create(usuario=usuario, **kwargs)


def criar_aluno_pcd(cpf, nome='Aluno PcD', **kwargs):
    return criar_aluno(
        cpf,
        nome=nome,
        deficiencia=TipoDeficiencia.DEFICIENCIA_FISICA,
        **kwargs,
    )


def criar_rota_e_execucao(vagas=1, dias_ate_execucao=7, horario_saida=time(12, 0)):
    data_execucao = timezone.localdate() + timedelta(days=dias_ate_execucao)
    percurso = Percurso.objects.create(
        apelido=f'Percurso {timezone.now().timestamp()}',
        descricao='Percurso de teste',
    )
    rota = Rota.objects.create(
        percurso=percurso,
        horario_saida=horario_saida,
        dia_semana=DIAS_POR_WEEKDAY[data_execucao.weekday()],
        quantidade_vagas=vagas,
    )
    execucao = ExecucaoRota().business.criar_execucao(rota.pk, data_execucao)
    return rota, execucao

