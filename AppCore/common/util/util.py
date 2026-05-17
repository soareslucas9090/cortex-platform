import logging
import re

from django.core.mail import EmailMultiAlternatives

from AppCore.core.exceptions.exceptions import SystemErrorException, ValidationException

logger = logging.getLogger(__name__)


def enviar_email_simples(subject, simple_text, from_email, to_emails, html_content):
    try:
        email = EmailMultiAlternatives(
            subject,
            simple_text,
            from_email,
            to_emails,
        )

        email.attach_alternative(html_content, "text/html")

        email.send()
    except Exception as err:
        logger.exception('Erro ao enviar email: %s', err)
        raise SystemErrorException('Erro ao enviar email.')


def normalizar_cpf(cpf: str) -> str:
    """Remove formatação do CPF, mantendo apenas os dígitos."""
    return re.sub(r'\D', '', cpf)


def formatar_cpf(cpf):
        """Formata o CPF (XXX.XXX.XXX-XX)."""
        if len(cpf) == 11:
            return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
        return cpf


def validar_senha(senha):
    """Valida a complexidade da senha."""
    if len(senha) < 8:
        raise ValidationException(
        "A senha deve ter pelo menos 8 caracteres."
        )
    
    if not re.search(r'[A-Z]', senha):
        raise ValidationException(
        "A senha deve conter pelo menos uma letra maiúscula."
        )
    
    if not re.search(r'[a-z]', senha):
        raise ValidationException(
        "A senha deve conter pelo menos uma letra minúscula."
        )
    
    if not re.search(r'\d', senha):
        raise ValidationException(
        "A senha deve conter pelo menos um número."
        )
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        raise ValidationException(
        "A senha deve conter pelo menos um caractere especial."
        )
    
    return senha