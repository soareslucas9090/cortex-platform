import sys
import subprocess
from django.core.management.base import BaseCommand
from django.utils import autoreload

class Command(BaseCommand):
    help = 'Roda o Celery Worker com autoreload do Django'

    def add_arguments(self, parser):
        # Permite passar quaisquer argumentos adicionais para o celery
        parser.add_argument(
            'celery_args',
            nargs='*',
            help='Argumentos adicionais para passar ao comando do Celery (ex: --pool=prefork)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando Celery Worker com Autoreload do Django...'))
        
        celery_args = options.get('celery_args', [])
        
        def run_celery():
            # Executa o celery como um módulo Python usando o executável atual
            cmd = [sys.executable, '-m', 'celery', '-A', 'Cortex', 'worker']
            
            # Adiciona nível de log padrão se não especificado
            if not any(arg.startswith('-l') or arg.startswith('--loglevel') for arg in celery_args):
                cmd += ['-l', 'INFO']
                
            # No Windows, se nenhum pool for definido, usa 'solo' por compatibilidade
            if sys.platform == 'win32' and not any(arg.startswith('--pool') for arg in celery_args):
                cmd += ['--pool', 'solo']
                
            # Adiciona os argumentos extras passados ao comando do django
            if celery_args:
                cmd += celery_args
                
            # Inicia o subprocesso do Celery
            p = subprocess.Popen(cmd)
            try:
                p.wait()
            except BaseException:
                # Garante que o worker do Celery seja encerrado se o Django reiniciar ou fechar
                p.terminate()
                p.wait()
                raise

        # Executa a função usando o autoreload do Django
        autoreload.run_with_reloader(run_celery)
