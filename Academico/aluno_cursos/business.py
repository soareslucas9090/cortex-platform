import logging

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import ValidationException

logger = logging.getLogger(__name__)


class AlunoCursoBusiness(ModelInstanceBusiness):

    def criar_vinculo(self, aluno_id: int, curso_id: int, **kwargs):
        """Cria um vínculo acadêmico entre aluno e curso, validando duplicidade."""
        try:
            from Academico.alunos.models import Aluno
            from Academico.cursos.models import Curso
            from AppCore.common.util.util import normalizar_matricula
            from .models import AlunoCurso
            try:
                aluno = Aluno.objects.get(pk=aluno_id)
            except Aluno.DoesNotExist:
                raise ValidationException('Aluno não encontrado.')
            try:
                curso = Curso.objects.get(pk=curso_id)
            except Curso.DoesNotExist:
                raise ValidationException('Curso não encontrado.')
            self.object_instance.rules.vinculo_unico_ativo(aluno=aluno, curso=curso)
            if 'matricula' in kwargs:
                kwargs['matricula'] = normalizar_matricula(kwargs['matricula'])
                if kwargs['matricula']:
                    self.object_instance.rules.matricula_unica(kwargs['matricula'])
            return AlunoCurso.objects.create(aluno=aluno, curso=curso, **kwargs)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar o vínculo acadêmico.', logger)

    def atualizar_dados(self, dados: dict):
        """Atualiza campos do vínculo (ex: ano_conclusao, ativo)."""
        try:
            from AppCore.common.util.util import normalizar_matricula

            if 'matricula' in dados:
                dados['matricula'] = normalizar_matricula(dados['matricula'])
                if dados['matricula']:
                    self.object_instance.rules.matricula_unica(
                        dados['matricula'],
                        excluir_id=self.object_instance.pk,
                    )
            for attr, value in dados.items():
                setattr(self.object_instance, attr, value)
            self.object_instance.save()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível atualizar o vínculo acadêmico.', logger)

    def encerrar(self, ano_conclusao: int):
        """Encerra o vínculo acadêmico, registrando o ano de conclusão."""
        try:
            self.object_instance.rules.pode_encerrar()
            self.object_instance.ativo = False
            self.object_instance.ano_conclusao = ano_conclusao
            self.object_instance.save(update_fields=['ativo', 'ano_conclusao'])
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível encerrar o vínculo acadêmico.', logger)
