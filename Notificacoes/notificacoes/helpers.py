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

    def obter_por_chave_idempotencia(self, destinatario_id, tipo, chave):
        from .models import Notificacao

        return Notificacao.objects.filter(
            destinatario_id=destinatario_id,
            tipo=tipo,
            chave_idempotencia=chave,
        ).first()

    def obter_envio_bloqueado(self, envio_id):
        from .models import Envio

        return (
            Envio.objects.select_for_update(of=('self',))
            .select_related('notificacao', 'notificacao__destinatario')
            .filter(pk=envio_id)
            .first()
        )

    def resumir_erro(self, exc):
        atual = exc
        visitados = set()
        while atual is not None and id(atual) not in visitados:
            visitados.add(id(atual))
            causa = atual.__cause__ or atual.__context__
            if causa is None:
                break
            atual = causa
        mensagem = (str(atual).strip() if atual is not None else '') or type(atual).__name__
        return f'{type(atual).__name__}: {mensagem}'[:500]
