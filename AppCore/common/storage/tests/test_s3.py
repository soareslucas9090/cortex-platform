from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings


class ObterClienteS3Tests(SimpleTestCase):
    @override_settings(
        AWS_S3_ENDPOINT_URL='https://t3.storage.dev',
        AWS_STORAGE_BUCKET_NAME='cortexbucket',
        AWS_ACCESS_KEY_ID='tid_x',
        AWS_SECRET_ACCESS_KEY='tsec_x',
        AWS_S3_REGION_NAME='auto',
    )
    @patch('AppCore.common.storage.s3.boto3.client')
    def test_cliente_usa_regiao_auto_e_checksum_quando_necessario(self, mock_client):
        from AppCore.common.storage.s3 import obter_cliente_s3

        mock_client.return_value = MagicMock()
        cliente, bucket = obter_cliente_s3()

        self.assertIs(cliente, mock_client.return_value)
        self.assertEqual(bucket, 'cortexbucket')
        kwargs = mock_client.call_args.kwargs
        self.assertEqual(kwargs['endpoint_url'], 'https://t3.storage.dev')
        self.assertEqual(kwargs['region_name'], 'auto')
        config = kwargs['config']
        self.assertEqual(config.signature_version, 's3v4')
        self.assertEqual(config.request_checksum_calculation, 'when_required')
        self.assertEqual(config.response_checksum_validation, 'when_required')

    @override_settings(
        AWS_S3_ENDPOINT_URL='https://t3.storage.dev',
        AWS_STORAGE_BUCKET_NAME='cortexbucket',
        AWS_ACCESS_KEY_ID='',
        AWS_SECRET_ACCESS_KEY='',
        AWS_S3_REGION_NAME='auto',
    )
    def test_credenciais_incompletas_nao_instanciam_cliente(self):
        from AppCore.common.storage.s3 import obter_cliente_s3

        cliente, bucket = obter_cliente_s3()
        self.assertIsNone(cliente)
        self.assertIsNone(bucket)


class ChaveSemNomeDoBucketTests(SimpleTestCase):
    @override_settings(AWS_STORAGE_BUCKET_NAME='Cortex')
    def test_normalizar_remove_bucket_de_chave_pura(self):
        from AppCore.common.storage.s3 import normalizar_chave_s3

        chave = normalizar_chave_s3(
            'Cortex/usuarios/fotos/1/abc.jpg',
            prefixo='usuarios/fotos',
        )
        self.assertEqual(chave, 'usuarios/fotos/1/abc.jpg')

    @override_settings(AWS_STORAGE_BUCKET_NAME='Cortex')
    def test_normalizar_mantem_chave_que_ja_esta_dentro_do_bucket(self):
        from AppCore.common.storage.s3 import normalizar_chave_s3

        chave = normalizar_chave_s3(
            'infraestrutura/recursos/fotos/4/abc.jpg',
            prefixo='infraestrutura/recursos/fotos',
        )
        self.assertEqual(chave, 'infraestrutura/recursos/fotos/4/abc.jpg')

    @override_settings(
        AWS_S3_ENDPOINT_URL='https://t3.storage.dev',
        AWS_STORAGE_BUCKET_NAME='Cortex',
        AWS_ACCESS_KEY_ID='tid_x',
        AWS_SECRET_ACCESS_KEY='tsec_x',
        AWS_S3_REGION_NAME='auto',
    )
    @patch('AppCore.common.storage.s3.boto3.client')
    @patch('AppCore.common.storage.s3.uuid.uuid4')
    def test_enviar_grava_e_devolve_chave_sem_nome_do_bucket(self, mock_uuid, mock_client):
        from AppCore.common.storage.s3 import enviar_arquivo_s3

        mock_uuid.return_value.hex = 'abc123'
        cliente = MagicMock()
        mock_client.return_value = cliente

        chave = enviar_arquivo_s3(
            'Cortex/usuarios/fotos',
            1,
            MagicMock(),
            extensao='jpg',
            content_type='image/jpeg',
        )

        self.assertEqual(chave, 'usuarios/fotos/1/abc123.jpg')
        cliente.upload_fileobj.assert_called_once()
        self.assertEqual(cliente.upload_fileobj.call_args.args[1], 'Cortex')
        self.assertEqual(cliente.upload_fileobj.call_args.args[2], 'usuarios/fotos/1/abc123.jpg')
