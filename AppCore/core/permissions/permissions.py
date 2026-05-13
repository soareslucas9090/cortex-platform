from rest_framework.permissions import AllowAny, BasePermission


class AllowAnyPermission(AllowAny):
    """
    Permissão que permite acesso a qualquer usuário, independentemente de autenticação.
    """
    pass


class IsOwnerOrAdminPermission(BasePermission):
    """
        Esta view permite que apenas o dono de um objeto ou um administrador acesse o recurso.
        Ela também permite acesso a qualquer usuário autenticado, mas restringe a ações que não interajam com nenhum objeto específico.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser or getattr(request.user, 'is_admin', False):
            return True
        
        usuario_proprietario = view.obter_usuario_dono(obj)
        
        return usuario_proprietario == request.user


class IsAdminPermission(BasePermission):
    """
    Permite acesso apenas a superusuários ou usuários com is_admin=True.
    O campo is_admin é opcional no modelo — usa getattr com fallback False.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not request.user.is_superuser and not getattr(request.user, 'is_admin', False):
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not request.user.is_superuser and not getattr(request.user, 'is_admin', False):
            return False
        
        return True
