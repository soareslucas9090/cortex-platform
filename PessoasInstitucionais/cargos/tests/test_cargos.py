from rest_framework.test import APITestCase

from AppCore.core.exceptions.exceptions import BusinessRuleException
from PessoasInstitucionais.cargos.models import Cargo


class CargoBusinessTestCase(APITestCase):
    
    def test_criar_cargo_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        self.assertEqual(cargo.nome, 'Professor')
        self.assertTrue(cargo.ativo)

    def test_criar_cargo_nome_duplicado(self):
        Cargo().business.criar_cargo(nome='Professor')
        with self.assertRaises(BusinessRuleException) as context:
            Cargo().business.criar_cargo(nome='Professor')
        self.assertIn('Já existe um cargo cadastrado com esse nome', str(context.exception))

    def test_atualizar_dados_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.atualizar_dados({'nome': 'Professor Titular'})
        cargo.refresh_from_db()
        self.assertEqual(cargo.nome, 'Professor Titular')

    def test_atualizar_dados_nome_duplicado(self):
        Cargo().business.criar_cargo(nome='Professor')
        cargo2 = Cargo().business.criar_cargo(nome='Técnico')
        with self.assertRaises(BusinessRuleException):
            cargo2.business.atualizar_dados({'nome': 'Professor'})

    def test_desativar_cargo_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.desativar()
        cargo.refresh_from_db()
        self.assertFalse(cargo.ativo)

    def test_desativar_cargo_ja_inativo(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.desativar()
        with self.assertRaises(BusinessRuleException):
            cargo.business.desativar()

    def test_reativar_cargo_sucesso(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        cargo.business.desativar()
        cargo.business.reativar()
        cargo.refresh_from_db()
        self.assertTrue(cargo.ativo)

    def test_reativar_cargo_ja_ativo(self):
        cargo = Cargo().business.criar_cargo(nome='Professor')
        with self.assertRaises(BusinessRuleException):
            cargo.business.reativar()
