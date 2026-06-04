class UserModelPermissionMixin:
    _user_permissions = None
    user_permissions_class = None

    @property
    def user_permissions(self):
        if not self._user_permissions:
            self._user_permissions = self.get_model_user_permissions_class()

        return self._user_permissions

    def get_model_user_permissions_class(self):
        if not self.user_permissions_class:
            raise ValueError('user_permissions_class não foi definido no model')
        return self.user_permissions_class(object_instance=self)
    
    @property
    def permissoes(self) -> dict:
        """
            Calcula as permissões do usuário para os módulos do frontend.
            Delega para a classe de permissões associada ao model.
        """
        return self.user_permissions.compilar_permissoes()
