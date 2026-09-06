from datetime import time, timedelta

from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from Academico.alunos.models import Aluno
from Identidade.usuarios.models import TipoDeficiencia, Usuario
from Organizacional.funcoes.models import Funcao
from Organizacional.setores.models import Setor
from Organizacional.vinculos.models import SetorVinculo
from PessoasInstitucionais.cargos.models import Cargo
from PessoasInstitucionais.empresas_instituicoes.models import EmpresaInstituicao
from PessoasInstitucionais.servidores.models import Servidor
from PessoasInstitucionais.terceirizados.models import Terceirizado
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.percursos.models import Percurso
from Transporte.permissoes.models import PermissaoFuncaoTransporte, PermissaoUsuarioTransporte
from Transporte.rotas.choices import DiaSemana
from Transporte.rotas.models import Rota


def criar_strike(ticket):
    from Transporte.strikes.helpers import sincronizar_faltas_transporte
    from Transporte.strikes.models import Strike

    strike = Strike.objects.create(ticket=ticket)
    sincronizar_faltas_transporte(ticket.aluno)
    return strike


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


def criar_conferente(cpf='30000000001', nome='Conferente', terceirizado=False):
    usuario = criar_usuario(cpf, nome=nome)
    funcao = Funcao.objects.create(
        papel_funcao=f'Conferente {cpf}',
        descricao='Conferente de transporte',
    )
    PermissaoFuncaoTransporte().business.criar_permissao(funcao.pk, conferir=True)
    setor = Setor.objects.create(nome=f'Transporte {cpf}', sigla=cpf[-5:])
    SetorVinculo.objects.create(usuario=usuario, setor=setor, funcao=funcao)
    if terceirizado:
        empresa = EmpresaInstituicao.objects.create(nome=f'Empresa {cpf}')
        Terceirizado.objects.create(
            usuario=usuario,
            empresa_instituicao=empresa,
            ativo=True,
        )
    else:
        cargo = Cargo.objects.create(nome=f'Cargo {cpf}')
        Servidor.objects.create(usuario=usuario, cargo=cargo, categoria=1, ativo=True)
    return usuario


def criar_conferente_por_usuario(cpf='30000000011', nome='Conferente usuário'):
    usuario = criar_usuario(cpf, nome=nome)
    cargo = Cargo.objects.create(nome=f'Cargo direto {cpf}')
    Servidor.objects.create(usuario=usuario, cargo=cargo, categoria=1, ativo=True)
    PermissaoUsuarioTransporte().business.criar_permissao(usuario.pk, conferir=True)
    return usuario


def criar_execucao_hoje(vagas=2, horario_saida=time(18, 0)):
    return criar_rota_e_execucao(
        vagas=vagas,
        dias_ate_execucao=0,
        horario_saida=horario_saida,
    )

