import logging

from AppCore.core.business.business import ModelInstanceBusiness
logger = logging.getLogger(__name__)


class CursoBusiness(ModelInstanceBusiness):

    def criar_curso(self, nome: str, codigo_curso: str, setor_id: int, **kwargs):
        """Cria um novo curso validando unicidade do código, setor e nível de ensino."""
        try:
            from .models import Curso
            self.object_instance.rules.nivel_ensino_valido(kwargs.get('nivel_ensino'))
            self.object_instance.rules.codigo_unico(codigo_curso)
            self.object_instance.rules.validar_setor_obrigatorio(setor_id)
            return Curso.objects.create(
                nome=nome,
                codigo_curso=codigo_curso,
                setor_id=setor_id,
                **kwargs,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o curso.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do curso. Revalida código, setor e nível quando informados."""
        try:
            if 'codigo_curso' in dados:
                self.object_instance.rules.codigo_unico(
                    dados['codigo_curso'],
                    excluir_id=self.object_instance.pk,
                )
            if 'setor_id' in dados:
                self.object_instance.rules.validar_setor_obrigatorio(dados['setor_id'])
            if 'nivel_ensino' in dados:
                self.object_instance.rules.nivel_ensino_valido(dados.get('nivel_ensino'))
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            if not self.object_instance.setor_id:
                self.object_instance.rules.validar_setor_obrigatorio(None)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o curso.', logger)

    def importar_curso(self, codigo_curso: str, nome: str, setor, ativo: bool = True):
        """Cria ou atualiza um curso pela chave natural codigo_curso, com setor obrigatório."""
        try:
            from .models import Curso

            setor_id = setor.pk if setor is not None else None
            self.object_instance.rules.validar_setor_obrigatorio(setor_id)

            nome_gravar = ' '.join((nome or '').strip().split())
            curso = self.object_instance.helper.obter_por_codigo_normalizado(codigo_curso)
            if curso:
                curso.nome = nome_gravar
                curso.setor = setor
                curso.ativo = ativo
                curso.save()
                return curso, False

            codigo_gravar = ' '.join((codigo_curso or '').strip().split())
            curso = Curso.objects.create(
                nome=nome_gravar,
                codigo_curso=codigo_gravar,
                setor=setor,
                ativo=ativo,
            )
            return curso, True
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível importar o curso.', logger)

    def desativar(self):
        """Desativa o curso."""
        try:
            self.object_instance.rules.pode_desativar()
            self.object_instance.ativo = False
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível desativar o curso.', logger)

    def reativar(self):
        """Reativa o curso."""
        try:
            self.object_instance.rules.pode_reativar()
            self.object_instance.ativo = True
            self.object_instance.save(update_fields=['ativo'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reativar o curso.', logger)
