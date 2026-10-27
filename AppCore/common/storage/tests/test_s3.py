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
