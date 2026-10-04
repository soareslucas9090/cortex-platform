from types import SimpleNamespace

from django.contrib import admin
from django.contrib.admin.utils import construct_change_message
from django.forms.models import inlineformset_factory
from django.test import TestCase

from Identidade.enderecos.models import Endereco
from Identidade.usuarios.admin import UsuarioAdmin
from Identidade.usuarios.models import Usuario


class UsuarioAdminEnderecoInlineTest(TestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            cpf='50000000001',
            password='Senha@123',
            nome='Usuário Admin',
        )
        self.endereco = Endereco.objects.create(
            usuario=self.usuario,
            logradouro='Rua Antiga',
            numero='10',
            complemento='',
            bairro='Centro',
            cep='64800000',
            cidade='Floriano',
            estado='PI',
        )
        self.usuario_admin = UsuarioAdmin(Usuario, admin.site)

    def test_salvar_inline_inicializa_controle_de_auditoria_do_formset(self):
        EnderecoFormSet = inlineformset_factory(
            Usuario,
            Endereco,
            fields=(
                'logradouro',
                'numero',
                'complemento',
                'bairro',
                'cep',
                'cidade',
                'estado',
            ),
            extra=0,
            can_delete=False,
        )
        prefixo = 'endereco_inline'
        formset = EnderecoFormSet(
            data={
                f'{prefixo}-TOTAL_FORMS': '1',
                f'{prefixo}-INITIAL_FORMS': '1',
                f'{prefixo}-MIN_NUM_FORMS': '0',
                f'{prefixo}-MAX_NUM_FORMS': '1',
                f'{prefixo}-0-id': str(self.endereco.pk),
                f'{prefixo}-0-logradouro': 'Rua Atualizada',
                f'{prefixo}-0-numero': '20',
                f'{prefixo}-0-complemento': '',
                f'{prefixo}-0-bairro': 'Centro',
                f'{prefixo}-0-cep': '64800000',
                f'{prefixo}-0-cidade': 'Floriano',
                f'{prefixo}-0-estado': 'PI',
            },
            instance=self.usuario,
            prefix=prefixo,
        )
        self.assertTrue(formset.is_valid(), formset.errors)

        formulario_usuario = SimpleNamespace(instance=self.usuario, changed_data=[])
        self.usuario_admin.save_formset(
            request=None,
            form=formulario_usuario,
            formset=formset,
            change=True,
        )

        self.endereco.refresh_from_db()
        self.assertEqual(self.endereco.logradouro, 'Rua Atualizada')
        self.assertEqual(self.endereco.numero, '20')
        self.assertEqual(formset.new_objects, [])
        self.assertEqual(formset.deleted_objects, [])
        self.assertEqual(len(formset.changed_objects), 1)

        mensagem = construct_change_message(
            formulario_usuario,
            [formset],
            add=False,
        )
        self.assertTrue(mensagem)
