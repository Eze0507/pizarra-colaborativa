"""Política central de acceso a proyectos de NodoBoard."""
from enum import StrEnum

from django.db.models import Q, QuerySet
from rest_framework.exceptions import PermissionDenied

from usuario.models import UserColaborador

from .models import Proyecto


class ProjectAction(StrEnum):
    READ = "read"
    EXPORT = "export"
    WRITE = "write"
    IMPORT = "import"
    MANAGE = "manage"
    DELETE = "delete"


ROLE_ACTIONS = {
    UserColaborador.Rol.PROPIETARIO: frozenset(ProjectAction),
    UserColaborador.Rol.EDITOR: frozenset({
        ProjectAction.READ,
        ProjectAction.EXPORT,
        ProjectAction.WRITE,
        ProjectAction.IMPORT,
    }),
    UserColaborador.Rol.VISUALIZADOR: frozenset({
        ProjectAction.READ,
        ProjectAction.EXPORT,
    }),
}


def get_project_role(user, proyecto: Proyecto) -> str | None:
    """Devuelve el rol efectivo; solo considera colaboraciones activas."""
    if not user or not user.is_authenticated:
        return None
    if proyecto.propietario_id == user.id:
        return UserColaborador.Rol.PROPIETARIO
    return UserColaborador.objects.filter(
        proyecto_id=proyecto.id,
        usuario_id=user.id,
        estado=UserColaborador.Estado.ACTIVO,
    ).values_list("rol", flat=True).first()


def user_can_project_action(user, proyecto: Proyecto, action: ProjectAction) -> bool:
    role = get_project_role(user, proyecto)
    return action in ROLE_ACTIONS.get(role, frozenset())


def user_id_can_project_action(user_id: int, proyecto_id: int, action: ProjectAction) -> bool:
    """Variante para Consumers, evitando transportar objetos User entre hilos."""
    proyecto = Proyecto.objects.filter(pk=proyecto_id).only("id", "propietario_id").first()
    if not proyecto:
        return False
    if proyecto.propietario_id == user_id:
        role = UserColaborador.Rol.PROPIETARIO
    else:
        role = UserColaborador.objects.filter(
            proyecto_id=proyecto_id,
            usuario_id=user_id,
            estado=UserColaborador.Estado.ACTIVO,
        ).values_list("rol", flat=True).first()
    return action in ROLE_ACTIONS.get(role, frozenset())


def require_project_action(user, proyecto: Proyecto, action: ProjectAction, message: str | None = None) -> None:
    if not user_can_project_action(user, proyecto, action):
        raise PermissionDenied(message or "No tienes permisos para realizar esta acción en el proyecto.")


def accessible_projects(user) -> QuerySet[Proyecto]:
    if not user or not user.is_authenticated:
        return Proyecto.objects.none()
    return Proyecto.objects.filter(
        Q(propietario=user)
        | Q(
            colaboradores_detalle__usuario=user,
            colaboradores_detalle__estado=UserColaborador.Estado.ACTIVO,
        )
    ).distinct()
