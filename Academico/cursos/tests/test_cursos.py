from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from AppCore.core.exceptions.exceptions import BusinessRuleException
from Identidade.usuarios.models import Usuario
from Organizacional.setores.models import Setor
from Academico.cursos.choices import NivelEnsino
from Academico.cursos.models import Curso


def obter_token(usuario):
    return str(RefreshToken.for_user(usuario).access_token)


def criar_admin(cpf='00000000001', nome='Admin'):
    return Usuario.objects.create_superuser(cpf=cpf, password='Senha@123', nome=nome)


def criar_setor(sigla='TCCRS', nome='Setor de Curso Teste'):
    setor, _ = Setor.objects.get_or_create(sigla=sigla, defaults={'nome': nome})
    return setor


def criar_curso(nome='Sistemas de Informação', codigo='SI-001', setor=None):
    if setor is None:
        setor = criar_setor()
    return Curso.objects.create(nome=nome, codigo_curso=codigo, setor=setor)


class CursoBusinessTestCase(APITestCase):

    def setUp(self):
        self.setor = criar_setor()

    def test_criar_curso_sucesso(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        self.assertEqual(curso.nome, 'Sistemas de Informação')
        self.assertEqual(curso.codigo_curso, 'SI-001')
        self.assertEqual(curso.setor_id, self.setor.pk)
        self.assertEqual(curso.nivel_ensino, NivelEnsino.SUPERIOR)
        self.assertTrue(curso.ativo)

    def test_criar_curso_sem_setor(self):
        with self.assertRaises(BusinessRuleException) as ctx:
            Curso().business.criar_curso(
                nome='Sistemas de Informação',
                codigo_curso='SI-001',
                setor_id=None,
                nivel_ensino=NivelEnsino.SUPERIOR,
            )
        self.assertIn('O curso deve possuir um setor associado', str(ctx.exception))

    def test_criar_curso_setor_inexistente(self):
        with self.assertRaises(BusinessRuleException) as ctx:
            Curso().business.criar_curso(
                nome='Sistemas de Informação',
                codigo_curso='SI-001',
                setor_id=999999,
                nivel_ensino=NivelEnsino.SUPERIOR,
            )
        self.assertIn('Setor associado ao curso não encontrado', str(ctx.exception))

    def test_criar_curso_sem_nivel(self):
        with self.assertRaises(BusinessRuleException) as ctx:
            Curso().business.criar_curso(
                nome='Sistemas de Informação',
                codigo_curso='SI-001',
                setor_id=self.setor.pk,
            )
        self.assertIn('nível de ensino válido', str(ctx.exception))

    def test_criar_curso_nivel_invalido(self):
        with self.assertRaises(BusinessRuleException) as ctx:
            Curso().business.criar_curso(
                nome='Sistemas de Informação',
                codigo_curso='SI-001',
                setor_id=self.setor.pk,
                nivel_ensino=99,
            )
        self.assertIn('nível de ensino válido', str(ctx.exception))

    def test_atualizar_nivel_ensino(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        curso.business.atualizar_dados({'nivel_ensino': NivelEnsino.ENSINO_MEDIO})
        curso.refresh_from_db()
        self.assertEqual(curso.nivel_ensino, NivelEnsino.ENSINO_MEDIO)

    def test_atualizar_nivel_invalido(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        with self.assertRaises(BusinessRuleException):
            curso.business.atualizar_dados({'nivel_ensino': 99})

    def test_criar_curso_codigo_duplicado(self):
        Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        with self.assertRaises(BusinessRuleException) as ctx:
            Curso().business.criar_curso(
                nome='Sistemas II',
                codigo_curso='SI-001',
                setor_id=self.setor.pk,
                nivel_ensino=NivelEnsino.SUPERIOR,
            )
        self.assertIn('Já existe um curso cadastrado com esse código', str(ctx.exception))

    def test_atualizar_dados_sucesso(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        curso.business.atualizar_dados({'nome': 'Ciência da Computação'})
        curso.refresh_from_db()
        self.assertEqual(curso.nome, 'Ciência da Computação')

    def test_atualizar_dados_codigo_duplicado(self):
        Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        curso2 = Curso().business.criar_curso(
            nome='Engenharia de Software',
            codigo_curso='ES-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        with self.assertRaises(BusinessRuleException):
            curso2.business.atualizar_dados({'codigo_curso': 'SI-001'})

    def test_atualizar_dados_mesmo_codigo(self):
        """Deve permitir atualizar sem mudar o código (excluindo o próprio da verificação)."""
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        curso.business.atualizar_dados({
            'nome': 'Sistemas de Informação Atualizado',
            'codigo_curso': 'SI-001',
        })
        curso.refresh_from_db()
        self.assertEqual(curso.nome, 'Sistemas de Informação Atualizado')

    def test_atualizar_nao_permite_remover_setor(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        with self.assertRaises(BusinessRuleException) as ctx:
            curso.business.atualizar_dados({'setor_id': None})
        self.assertIn('O curso deve possuir um setor associado', str(ctx.exception))

    def test_atualizar_curso_legado_sem_setor_exige_setor(self):
        curso = Curso.objects.create(nome='Curso Legado', codigo_curso='LEG-1')
        with self.assertRaises(BusinessRuleException) as ctx:
            curso.business.atualizar_dados({'nome': 'Curso Legado Atualizado'})
        self.assertIn('O curso deve possuir um setor associado', str(ctx.exception))

        curso.business.atualizar_dados({'setor_id': self.setor.pk})
        curso.refresh_from_db()
        self.assertEqual(curso.setor_id, self.setor.pk)

    def test_desativar_curso_sucesso(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        curso.business.desativar()
        curso.refresh_from_db()
        self.assertFalse(curso.ativo)

    def test_desativar_curso_ja_inativo(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        curso.business.desativar()
        with self.assertRaises(BusinessRuleException):
            curso.business.desativar()

    def test_reativar_curso_sucesso(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        curso.business.desativar()
        curso.business.reativar()
        curso.refresh_from_db()
        self.assertTrue(curso.ativo)

    def test_reativar_curso_ja_ativo(self):
        curso = Curso().business.criar_curso(
            nome='Sistemas de Informação',
            codigo_curso='SI-001',
            setor_id=self.setor.pk,
            nivel_ensino=NivelEnsino.SUPERIOR,
        )
        with self.assertRaises(BusinessRuleException):
            curso.business.reativar()


class CursosAPITestCase(APITestCase):

    def setUp(self):
        Curso.objects.all().delete()
        self.admin = criar_admin()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(self.admin)}')
        self.setor = criar_setor()
        self.curso = criar_curso(setor=self.setor)

    def test_listar_cursos(self):
        url = reverse('academico:curso-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)
        self.assertEqual(response.data['dados'][0]['setor_id'], self.setor.pk)
        self.assertEqual(response.data['dados'][0]['setor_sigla'], self.setor.sigla)
        self.assertEqual(response.data['dados'][0]['setor_nome'], self.setor.nome)

    def test_listar_cursos_filtrar_ativo(self):
        url = reverse('academico:curso-list')
        response = self.client.get(url, {'ativo': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_listar_cursos_filtrar_inativo(self):
        self.curso.business.desativar()
        url = reverse('academico:curso-list')
        response = self.client.get(url, {'ativo': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)

    def test_listar_cursos_filtrar_setor_id(self):
        outro_setor = criar_setor(sigla='FILT', nome='Setor Filtro')
        criar_curso(nome='Outro Curso', codigo='OT-001', setor=outro_setor)
        url = reverse('academico:curso-list')
        response = self.client.get(url, {'setor_id': self.setor.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)
        self.assertEqual(response.data['dados'][0]['codigo_curso'], 'SI-001')

    def test_criar_curso(self):
        url = reverse('academico:curso-list')
        payload = {
            'nome': 'Engenharia de Software',
            'codigo_curso': 'ES-001',
            'setor_id': self.setor.pk,
            'nivel_ensino': NivelEnsino.SUPERIOR,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['dados']['nivel_ensino'], NivelEnsino.SUPERIOR)
        self.assertEqual(response.data['dados']['nivel_ensino_display'], 'Superior')
        curso = Curso.objects.get(codigo_curso='ES-001')
        self.assertEqual(curso.setor_id, self.setor.pk)

    def test_criar_curso_sem_setor(self):
        url = reverse('academico:curso-list')
        payload = {
            'nome': 'Engenharia de Software',
            'codigo_curso': 'ES-001',
            'nivel_ensino': NivelEnsino.SUPERIOR,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_curso_sem_nivel(self):
        url = reverse('academico:curso-list')
        payload = {
            'nome': 'Engenharia de Software',
            'codigo_curso': 'ES-002',
            'setor_id': self.setor.pk,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_curso_nivel_invalido(self):
        url = reverse('academico:curso-list')
        payload = {
            'nome': 'Engenharia de Software',
            'codigo_curso': 'ES-003',
            'setor_id': self.setor.pk,
            'nivel_ensino': 99,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_nivel_ensino(self):
        url = reverse('academico:curso-detail', kwargs={'pk': self.curso.pk})
        response = self.client.patch(url, {'nivel_ensino': NivelEnsino.TECNICO}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertEqual(self.curso.nivel_ensino, NivelEnsino.TECNICO)

    def test_listar_cursos_filtrar_nivel_ensino(self):
        Curso.objects.create(
            nome='Ensino Médio',
            codigo_curso='EM-001',
            nivel_ensino=NivelEnsino.ENSINO_MEDIO,
        )
        url = reverse('academico:curso-list')
        response = self.client.get(url, {'nivel_ensino': NivelEnsino.ENSINO_MEDIO})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['dados']), 1)
        self.assertEqual(response.data['dados'][0]['codigo_curso'], 'EM-001')

    def test_criar_curso_codigo_duplicado(self):
        url = reverse('academico:curso-list')
        payload = {
            'nome': 'Outro Curso',
            'codigo_curso': 'SI-001',
            'setor_id': self.setor.pk,
            'nivel_ensino': NivelEnsino.SUPERIOR,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhar_curso(self):
        url = reverse('academico:curso-detail', kwargs={'pk': self.curso.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dados']['codigo_curso'], 'SI-001')
        self.assertEqual(response.data['dados']['setor_id'], self.setor.pk)

    def test_atualizar_curso(self):
        url = reverse('academico:curso-detail', kwargs={'pk': self.curso.pk})
        payload = {'nome': 'Sistemas de Informação - Atualizado'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertEqual(self.curso.nome, 'Sistemas de Informação - Atualizado')

    def test_atualizar_curso_trocar_setor(self):
        outro_setor = criar_setor(sigla='TROCA', nome='Setor Troca')
        url = reverse('academico:curso-detail', kwargs={'pk': self.curso.pk})
        payload = {'setor_id': outro_setor.pk}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertEqual(self.curso.setor_id, outro_setor.pk)

    def test_atualizar_curso_nao_permite_setor_nulo(self):
        url = reverse('academico:curso-detail', kwargs={'pk': self.curso.pk})
        payload = {'setor_id': None}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_curso_legado_sem_setor(self):
        legado = Curso.objects.create(nome='Curso Legado', codigo_curso='LEG-API')
        url = reverse('academico:curso-detail', kwargs={'pk': legado.pk})
        response = self.client.patch(url, {'nome': 'Curso Legado Novo'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.patch(url, {'setor_id': self.setor.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        legado.refresh_from_db()
        self.assertEqual(legado.setor_id, self.setor.pk)

    def test_desativar_curso(self):
        url = reverse('academico:curso-desativar', kwargs={'pk': self.curso.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertFalse(self.curso.ativo)

    def test_reativar_curso(self):
        self.curso.business.desativar()
        url = reverse('academico:curso-reativar', kwargs={'pk': self.curso.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.curso.refresh_from_db()
        self.assertTrue(self.curso.ativo)

    def test_nao_autenticado_retorna_401(self):
        self.client.credentials()
        url = reverse('academico:curso-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_autenticado_pode_listar_catalogo(self):
        usuario_comum = Usuario.objects.create_user(cpf='00000000002', password='Senha@123', nome='Comum')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {obter_token(usuario_comum)}')
        url = reverse('academico:curso-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CursoSeedTestCase(APITestCase):

    def test_seed_permanece_sem_nivel(self):
        curso = Curso.objects.get(codigo_curso='14LMAT')
        self.assertIsNone(curso.nivel_ensino)
