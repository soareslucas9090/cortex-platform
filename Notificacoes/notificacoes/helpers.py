from AppCore.core.helpers.helpers import ModelInstanceHelpers


class NotificacaoHelpers(ModelInstanceHelpers):

    def resolver_email_destinatario(self, usuario):
        email = (getattr(usuario, 'email', None) or '').strip()
        if email:
            return email

        from Identidade.contatos.models import Contato

        contatos = list(Contato.objects.filter(usuario=usuario).order_by('pk'))
        for contato in contatos:
            academico = (contato.email_academico or '').strip()
            if academico:
                return academico
        for contato in contatos:
            pessoal = (contato.email_pessoal or '').strip()
            if pessoal:
                return pessoal
        return None

    def listar_do_destinatario(self, destinatario_id):
        from .models import Notificacao

        return Notificacao.objects.filter(destinatario_id=destinatario_id)

    def contar_nao_lidas(self, destinatario_id):
        return self.listar_do_destinatario(destinatario_id).filter(lida_em__isnull=True).count()
