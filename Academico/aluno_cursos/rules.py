from AppCore.core.rules.rules import ModelInstanceRules


class AlunoCursoRules(ModelInstanceRules):

    def vinculo_unico_ativo(self, aluno, curso) -> bool:
        """Valida que não existe já um vínculo ativo do mesmo aluno no mesmo curso."""
        from .models import AlunoCurso
        if AlunoCurso.objects.filter(aluno=aluno, curso=curso, ativo=True).exists():
            self.return_exception(
                'Este aluno já possui um vínculo ativo com este curso.'
            )
        return True

    def pode_encerrar(self) -> bool:
        """Vínculo só pode ser encerrado se estiver ativo."""
        if not self.object_instance.ativo:
            self.return_exception('Este vínculo já está encerrado.')
        return True
