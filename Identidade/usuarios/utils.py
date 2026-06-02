from AppCore.core.exceptions.exceptions import SystemErrorException


def normalizar_deficiencia(deficiencia: str):
    from Identidade.usuarios.models import TipoDeficiencia

    try:
        import unicodedata
        # 1. Remover acentos
        val_sem_acento = unicodedata.normalize('NFKD', str(deficiencia)).encode('ascii', 'ignore').decode('utf-8')
        # 2. Caixa baixa e substituir espaços por _
        val_normalizado = '_'.join(word for word in val_sem_acento.lower().split() if word)
        
        # 3. Mapear nos choices
        valid_choices = [choice[0] for choice in TipoDeficiencia.choices]

        if val_normalizado in valid_choices:
            return val_normalizado
        return None
    except Exception as e:
        raise SystemErrorException('Não foi possível normalizar a deficiência.')