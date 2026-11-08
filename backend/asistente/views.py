from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .serializers import EnviarConsultaAgenteSeniorSerializer
from .services import AsistenteServiceError
from .services.diagrama_imagen_service import DiagramaImagenService
from .services.instruccion_asistente_service import InstruccionAsistenteService
from .services.agente_senior_service import AgenteSeniorService


class GenerarDiagramaDesdeImagenView(APIView):
    """
    Endpoint para procesar imágenes de diagramas dibujados a mano
    mediante Google Gemini y transformarlos en estructura JSON de entidades y relaciones.
    Toda la lógica reside en DiagramaImagenService (services/diagrama_imagen_service.py).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        try:
            resultado = DiagramaImagenService.generar_desde_request(
                files=request.FILES,
                data=request.data
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except AsistenteServiceError as exc:
            return Response(exc.to_dict(), status=exc.status_code)


class EjecutarInstruccionAsistenteView(APIView):
    """
    Endpoint para procesar comandos/instrucciones breves de modelado en lenguaje natural
    y devolver un delta de acciones sobre el diagrama.
    Toda la lógica reside en InstruccionAsistenteService (services/instruccion_asistente_service.py).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        try:
            resultado = InstruccionAsistenteService.ejecutar_instruccion(data=request.data)
            return Response(resultado, status=status.HTTP_200_OK)
        except AsistenteServiceError as exc:
            return Response(exc.to_dict(), status=exc.status_code)


class AgenteSeniorConversacionView(APIView):
    """
    Vista delgada para el caso de uso «INTERACTUAR CON AGENTE SENIOR COLABORATIVO».
    Delega toda la lógica de negocio a AgenteSeniorService en services/agente_senior_service.py:
    - GET: Obtiene el historial de mensajes compartidos y el estado actual de la cola del proyecto.
    - POST: Valida, registra/encola (FIFO máx. 1 procesando + 2 en espera) y procesa una consulta
            contextualizada con el Agente Senior Colaborativo, sincronizando por WebSocket.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request, proyecto_id: int, *args, **kwargs):
        try:
            resultado = AgenteSeniorService.obtener_historial_proyecto(
                proyecto_id=proyecto_id,
                user=request.user
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except AsistenteServiceError as exc:
            return Response(exc.to_dict(), status=exc.status_code)

    def post(self, request, proyecto_id: int, *args, **kwargs):
        serializer = EnviarConsultaAgenteSeniorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contenido = serializer.validated_data.get('contenido') or serializer.validated_data.get('mensaje')
        contexto_diagrama = serializer.validated_data.get('contexto_diagrama')
        usar_ia_local = bool(serializer.validated_data.get('usar_ia_local', False))

        try:
            resultado = AgenteSeniorService.enviar_consulta(
                proyecto_id=proyecto_id,
                user=request.user,
                contenido=contenido,
                contexto_diagrama=contexto_diagrama,
                usar_ia_local=usar_ia_local
            )
            return Response(resultado, status=status.HTTP_201_CREATED)
        except AsistenteServiceError as exc:
            return Response(exc.to_dict(), status=exc.status_code)
