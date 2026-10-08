import os

bind = '0.0.0.0:8000'
workers = int(os.environ.get('WEB_CONCURRENCY', '3'))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '60'))
graceful_timeout = 30
keepalive = 5
accesslog = '-'
errorlog = '-'
capture_output = True
