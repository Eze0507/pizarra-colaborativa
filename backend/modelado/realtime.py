"""
Módulo de intermediación en tiempo real para proyectos de modelado.
Utiliza Redis Channel Layers para retransmitir instantáneamente eventos
de exclusión mutua, movimiento de entidades y cambios conceptuales
entre todos los colaboradores conectados a un mismo proyecto.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def get_proyecto_group_name(proyecto_id: int | str) -> str:
    """
    Retorna el identificador del grupo de canales en Redis para un proyecto específico.
    Ejemplo: 'pizarra_1'.
    """
    return f"pizarra_{proyecto_id}"


def notificar_evento_proyecto_sync(proyecto_id: int | str, tipo_evento: str, payload: dict):
    """
    Emite un evento sincrónicamente a todos los colaboradores del proyecto a través de Redis.
    Adecuado para invocar desde vistas DRF, signals del ORM o tareas auxiliares.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    grupo = get_proyecto_group_name(proyecto_id)
    async_to_sync(channel_layer.group_send)(
        grupo,
        {
            "type": "pizarra.evento",
            "evento": tipo_evento,
            "data": payload
        }
    )


async def notificar_evento_proyecto_async(proyecto_id: int | str, tipo_evento: str, payload: dict):
    """
    Emite un evento asincrónicamente a todos los colaboradores del proyecto a través de Redis.
    Adecuado para invocar dentro de los Consumers WebSocket de Django Channels.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    grupo = get_proyecto_group_name(proyecto_id)
    await channel_layer.group_send(
        grupo,
        {
            "type": "pizarra.evento",
            "evento": tipo_evento,
            "data": payload
        }
    )
