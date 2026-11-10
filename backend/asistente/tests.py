import json
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings

from modelado.models import Entidad, Proyecto

from .models import Conversacion, Mensaje
from .services import (
    AsistenteServiceError,
    GeminiProviderService,
    InstruccionAsistenteService,
    OllamaProviderService,
)
from .services.agente_senior_service import (
    AgenteSeniorService,
    ResultadoAgenteSenior,
    SYSTEM_PROMPT_AGENTE_SENIOR,
    TipoConsultaAgenteSenior,
)


class ClasificacionConsultaTests(SimpleTestCase):
    def test_clasifica_intenciones_principales_y_mensajes_mixtos(self):
        casos = {
            'hola': TipoConsultaAgenteSenior.SOCIAL,
            'gracias': TipoConsultaAgenteSenior.SOCIAL,
            '¿qué es una asociación UML?': TipoConsultaAgenteSenior.GENERAL_UML,
            'revisa mi diagrama': TipoConsultaAgenteSenior.DIAGRAM_SPECIFIC,
            'hola, revisa mis clases': TipoConsultaAgenteSenior.DIAGRAM_SPECIFIC,
            'gracias, revisa también las relaciones': TipoConsultaAgenteSenior.DIAGRAM_SPECIFIC,
            '¿y eso por qué?': TipoConsultaAgenteSenior.FOLLOW_UP,
        }

        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(AgenteSeniorService.clasificar_consulta(texto), esperado)


class ContextoInstruccionAsistenteTests(SimpleTestCase):
    @patch.object(
        GeminiProviderService,
        'generar_contenido',
        return_value='{"mensaje":"ok","entidades_a_crear":[],"entidades_a_modificar":[],"entidades_a_eliminar":[],"relaciones_a_crear":[],"relaciones_a_eliminar":[]}',
    )
    def test_cardinalidades_llegan_al_prompt_del_proveedor(self, generar_mock):
        InstruccionAsistenteService.ejecutar_instruccion({
            'instruccion': 'conserva la relacion',
            'contexto_diagrama': {
                'entidades': [],
                'relaciones': [{
                    'id': 8,
                    'entidad_origen_id': 1,
                    'entidad_destino_id': 2,
                    'tipo': 'asociacion',
                    'nombre_relacion': 'contiene',
                    'cardinalidad_origen': '1',
                    'cardinalidad_destino': '0..*',
                }],
            },
        })

        prompt = generar_mock.call_args.kwargs['contents'][0]
        self.assertIn('"cardinalidad_origen": "1"', prompt)
        self.assertIn('"cardinalidad_destino": "0..*"', prompt)


@override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='gemini-principal')
class GeminiProviderServiceTests(SimpleTestCase):
    @patch.object(
        GeminiProviderService,
        'obtener_modelos_candidatos',
        return_value=['gemini-principal', 'gemini-secundario'],
    )
    @patch('asistente.services.genai.Client')
    def test_chat_usa_turnos_reales_y_conserva_modelo_efectivo(
        self,
        client_mock,
        _modelos_mock,
    ):
        generar = client_mock.return_value.models.generate_content
        generar.side_effect = [
            SimpleNamespace(text=''),
            SimpleNamespace(text='Respuesta útil'),
        ]

        resultado = GeminiProviderService.generar_chat_con_metadatos(
            turnos=[
                {'role': 'user', 'content': 'Pregunta anterior'},
                {'role': 'model', 'content': 'Respuesta anterior'},
                {'role': 'user', 'content': 'Pregunta actual'},
            ],
            system_instruction='Instrucciones de prueba',
            temperature=0.3,
        )

        self.assertEqual(resultado['text'], 'Respuesta útil')
        self.assertEqual(resultado['model'], 'gemini-secundario')
        self.assertEqual(resultado['provider'], 'gemini')
        self.assertEqual(generar.call_count, 2)
        contenidos = generar.call_args.kwargs['contents']
        self.assertEqual([contenido.role for contenido in contenidos], ['user', 'model', 'user'])

    @patch.object(
        GeminiProviderService,
        'obtener_modelos_candidatos',
        return_value=['gemini-principal'],
    )
    @patch('asistente.services.genai.Client')
    def test_generar_contenido_conserva_retorno_string(
        self,
        client_mock,
        _modelos_mock,
    ):
        client_mock.return_value.models.generate_content.return_value = SimpleNamespace(
            text='contrato existente'
        )

        resultado = GeminiProviderService.generar_contenido(
            contents=['entrada existente'],
            system_instruction='sistema',
        )

        self.assertIsInstance(resultado, str)
        self.assertEqual(resultado, 'contrato existente')

    @patch.object(
        GeminiProviderService,
        'obtener_modelos_candidatos',
        return_value=['gemini-principal', 'gemini-secundario'],
    )
    @patch('asistente.services.genai.Client')
    def test_timeout_de_transporte_prueba_el_siguiente_modelo(
        self,
        client_mock,
        _modelos_mock,
    ):
        request = httpx.Request('POST', 'https://example.invalid')
        client_mock.return_value.models.generate_content.side_effect = [
            httpx.ReadTimeout('timeout', request=request),
            SimpleNamespace(text='respuesta posterior'),
        ]

        resultado = GeminiProviderService.generar_chat_con_metadatos(
            turnos=[{'role': 'user', 'content': 'consulta'}],
            system_instruction='sistema',
        )

        self.assertEqual(resultado['model'], 'gemini-secundario')


class ContextoGeminiTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='ana',
            password='test',
            first_name='Ana',
        )
        self.proyecto = Proyecto.objects.create(
            nombre='Proyecto de prueba',
            propietario=self.usuario,
        )
        self.conversacion = Conversacion.objects.create(proyecto=self.proyecto)
        Entidad.objects.create(proyecto=self.proyecto, nombre='Cliente')

    def crear_mensaje(self, contenido, rol=Mensaje.Rol.USER, estado=Mensaje.Estado.RESPONDIDO, pregunta=None):
        return Mensaje.objects.create(
            conversacion=self.conversacion,
            usuario=self.usuario if rol == Mensaje.Rol.USER else None,
            pregunta=pregunta,
            rol=rol,
            estado=estado,
            contenido=contenido,
        )

    def test_saludo_no_incluye_diagrama_y_mensaje_actual_aparece_una_vez(self):
        actual = self.crear_mensaje('hola', estado=Mensaje.Estado.PROCESANDO)

        contexto = AgenteSeniorService.construir_contexto_gemini(
            self.proyecto.id,
            self.conversacion.id,
            actual,
        )

        self.assertEqual(contexto['clasificacion'], TipoConsultaAgenteSenior.SOCIAL.value)
        self.assertFalse(contexto['incluye_diagrama'])
        contenido_total = '\n'.join(turno['content'] for turno in contexto['turnos'])
        self.assertNotIn('diagrama_uml', contenido_total)
        self.assertEqual(contenido_total.count('hola'), 1)
        self.assertEqual(contexto['turnos'][-1]['role'], 'user')

    def test_consulta_especifica_incluye_diagrama(self):
        actual = self.crear_mensaje(
            'revisa mi diagrama',
            estado=Mensaje.Estado.PROCESANDO,
        )

        contexto = AgenteSeniorService.construir_contexto_gemini(
            self.proyecto.id,
            self.conversacion.id,
            actual,
        )

        self.assertTrue(contexto['incluye_diagrama'])
        self.assertIn('diagrama_uml', contexto['turnos'][-1]['content'])
        self.assertIn('Cliente', contexto['turnos'][-1]['content'])

    def test_seguimiento_conceptual_conserva_turnos_sin_diagrama(self):
        pregunta = self.crear_mensaje('¿qué es una composición UML?')
        self.crear_mensaje(
            'Es una relación de pertenencia fuerte.',
            rol=Mensaje.Rol.AGENT,
            pregunta=pregunta,
        )
        actual = self.crear_mensaje(
            '¿y eso por qué?',
            estado=Mensaje.Estado.PROCESANDO,
        )

        contexto = AgenteSeniorService.construir_contexto_gemini(
            self.proyecto.id,
            self.conversacion.id,
            actual,
        )

        self.assertFalse(contexto['incluye_diagrama'])
        self.assertEqual(
            [turno['role'] for turno in contexto['turnos']],
            ['user', 'model', 'user'],
        )

    def test_seguimiento_de_analisis_conserva_diagrama(self):
        pregunta = self.crear_mensaje('revisa mi diagrama')
        self.crear_mensaje(
            'La entidad Cliente necesita una clave.',
            rol=Mensaje.Rol.AGENT,
            pregunta=pregunta,
        )
        actual = self.crear_mensaje(
            '¿cómo la corrijo?',
            estado=Mensaje.Estado.PROCESANDO,
        )

        contexto = AgenteSeniorService.construir_contexto_gemini(
            self.proyecto.id,
            self.conversacion.id,
            actual,
        )

        self.assertTrue(contexto['incluye_diagrama'])
        self.assertIn('diagrama_uml', contexto['turnos'][-1]['content'])


class SeleccionProveedorTests(SimpleTestCase):
    @patch.object(OllamaProviderService, 'obtener_modelo_local', return_value='qwen-test')
    @patch.object(OllamaProviderService, 'generar_contenido', return_value='respuesta local')
    @patch.object(AgenteSeniorService, 'construir_prompt_con_contexto', return_value='prompt compacto')
    @patch.object(GeminiProviderService, 'generar_chat_con_metadatos')
    def test_ia_local_conserva_llamada_actual_de_ollama(
        self,
        gemini_mock,
        constructor_mock,
        ollama_mock,
        _modelo_mock,
    ):
        mensaje = SimpleNamespace(id=7)

        resultado = AgenteSeniorService._generar_respuesta_agente_senior(
            proyecto_id=1,
            conversacion_id=2,
            mensaje_pregunta=mensaje,
            usar_ia_local=True,
        )

        gemini_mock.assert_not_called()
        constructor_mock.assert_called_once_with(
            proyecto_id=1,
            conversacion_id=2,
            mensaje_pregunta=mensaje,
            compacto_para_local=True,
        )
        ollama_mock.assert_called_once()
        self.assertEqual(ollama_mock.call_args.kwargs['prompt'], 'prompt compacto')
        self.assertEqual(
            ollama_mock.call_args.kwargs['system_instruction'],
            SYSTEM_PROMPT_AGENTE_SENIOR,
        )
        self.assertEqual(ollama_mock.call_args.kwargs['temperature'], 0.3)
        self.assertEqual(resultado.provider, 'ollama')
        self.assertFalse(resultado.fallback_used)

    @patch.object(OllamaProviderService, 'obtener_modelo_local', return_value='qwen-test')
    @patch.object(OllamaProviderService, 'generar_contenido', return_value='respuesta de respaldo')
    @patch.object(AgenteSeniorService, 'construir_prompt_con_contexto', return_value='prompt compacto')
    @patch.object(
        GeminiProviderService,
        'generar_chat_con_metadatos',
        side_effect=AsistenteServiceError('sin disponibilidad', codigo='gemini_no_disponible'),
    )
    @patch.object(
        AgenteSeniorService,
        'construir_contexto_gemini',
        return_value={'turnos': [{'role': 'user', 'content': 'hola'}]},
    )
    def test_fallo_controlado_de_gemini_activa_respaldo(
        self,
        _contexto_mock,
        _gemini_mock,
        constructor_mock,
        ollama_mock,
        _modelo_mock,
    ):
        mensaje = SimpleNamespace(id=8)

        resultado = AgenteSeniorService._generar_respuesta_agente_senior(
            proyecto_id=1,
            conversacion_id=2,
            mensaje_pregunta=mensaje,
            usar_ia_local=False,
        )

        constructor_mock.assert_called_once_with(
            proyecto_id=1,
            conversacion_id=2,
            mensaje_pregunta=mensaje,
            compacto_para_local=True,
        )
        ollama_mock.assert_called_once()
        self.assertEqual(resultado.provider, 'ollama')
        self.assertTrue(resultado.fallback_used)

    @patch.object(OllamaProviderService, 'generar_contenido')
    @patch.object(
        GeminiProviderService,
        'generar_chat_con_metadatos',
        side_effect=ValueError('error interno'),
    )
    @patch.object(
        AgenteSeniorService,
        'construir_contexto_gemini',
        return_value={'turnos': [{'role': 'user', 'content': 'hola'}]},
    )
    def test_error_interno_no_se_oculta_con_ollama(
        self,
        _contexto_mock,
        _gemini_mock,
        ollama_mock,
    ):
        with self.assertRaisesRegex(ValueError, 'error interno'):
            AgenteSeniorService._generar_respuesta_agente_senior(
                proyecto_id=1,
                conversacion_id=2,
                mensaje_pregunta=SimpleNamespace(id=9),
                usar_ia_local=False,
            )

        ollama_mock.assert_not_called()

    def test_metadatos_publicos_no_incluyen_intentos_internos(self):
        resultado = ResultadoAgenteSenior(
            text='respuesta',
            provider='gemini',
            model='gemini-test',
            fallback_used=False,
            duration_ms=25,
        )

        self.assertEqual(resultado.metadatos_publicos(), {
            'provider': 'gemini',
            'model': 'gemini-test',
            'fallback_used': False,
            'duration_ms': 25,
        })


class AyudaAsistenteTests(SimpleTestCase):
    @patch.object(
        GeminiProviderService,
        'generar_contenido',
        return_value=json.dumps({
            "explicacion": "Para registrar un nuevo proyecto...",
            "pasos": [
                "1. Presiona el botón '+ Crear un nuevo proyecto'.",
                "2. Escribe el nombre en el modal.",
                "3. Presiona 'Crear proyecto'."
            ],
            "componente_id": "btn-crear-proyecto",
            "requiere_cambio_vista": False,
            "vista_destino": None
        })
    )
    def test_ayuda_proceso_dashboard_exitoso(self, mock_gemini):
        from .services import AyudaAsistenteService
        res = AyudaAsistenteService.consultar_ayuda("¿Cómo creo un proyecto?", "dashboard")
        self.assertEqual(res["componente_id"], "btn-crear-proyecto")
        self.assertFalse(res["requiere_cambio_vista"])
        self.assertEqual(len(res["pasos"]), 3)
        self.assertIn("Para registrar un nuevo proyecto", res["explicacion"])

    @patch.object(
        GeminiProviderService,
        'generar_contenido',
        return_value=json.dumps({
            "explicacion": "La generación de código Spring Boot se ejecuta dentro de la Pizarra.",
            "pasos": [
                "1. Abre un proyecto haciendo clic en 'Abrir →'.",
                "2. En la pizarra, haz clic en 'Generación Java · Spring Boot'."
            ],
            "componente_id": "btn-abrir-proyecto",
            "requiere_cambio_vista": True,
            "vista_destino": "pizarra"
        })
    )
    def test_ayuda_proceso_cambio_vista_pizarra(self, mock_gemini):
        from .services import AyudaAsistenteService
        res = AyudaAsistenteService.consultar_ayuda("¿Cómo genero backend Spring Boot?", "dashboard")
        self.assertEqual(res["componente_id"], "btn-abrir-proyecto")
        self.assertTrue(res["requiere_cambio_vista"])
        self.assertEqual(res["vista_destino"], "pizarra")

    def test_ayuda_consulta_vacia_lanza_error(self):
        from .services import AyudaAsistenteService
        with self.assertRaises(AsistenteServiceError) as ctx:
            AyudaAsistenteService.consultar_ayuda("   ", "dashboard")
        self.assertEqual(ctx.exception.codigo, "consulta_vacia")

    @patch.object(
        GeminiProviderService,
        'generar_contenido',
        return_value=json.dumps({
            "explicacion": "El dashboard te permite administrar proyectos.",
            "pasos": [],
            "componente_id": "id-inexistente-inventado",
            "requiere_cambio_vista": False,
            "vista_destino": None
        })
    )
    def test_ayuda_componente_invalido_se_limpia(self, mock_gemini):
        from .services import AyudaAsistenteService
        res = AyudaAsistenteService.consultar_ayuda("¿Qué es esto?", "dashboard")
        self.assertIsNone(res["componente_id"])

    def test_endpoint_consultar_ayuda_requiere_autenticacion(self):
        from rest_framework.test import APIClient
        client = APIClient()
        resp = client.post('/api/asistente/ayuda/', {'consulta': 'hola', 'interfaz': 'dashboard'}, format='json')
        self.assertEqual(resp.status_code, 401)

    @patch.object(
        GeminiProviderService,
        'generar_contenido',
        return_value=json.dumps({
            "explicacion": "Para crear una entidad en la pizarra, arrastra la tarjeta de Entidad al lienzo.",
            "pasos": [
                "1. Ubica el panel lateral izquierdo en la pestaña de Elementos.",
                "2. Arrastra la tarjeta 'card-nueva-entidad' hacia la pizarra."
            ],
            "componente_id": "card-nueva-entidad",
            "requiere_cambio_vista": False,
            "vista_destino": None
        })
    )
    def test_ayuda_proceso_pizarra_exitoso(self, mock_gemini):
        from .services import AyudaAsistenteService
        res = AyudaAsistenteService.consultar_ayuda("¿Cómo creo una entidad?", "pizarra")
        self.assertEqual(res["componente_id"], "card-nueva-entidad")
        self.assertFalse(res["requiere_cambio_vista"])
        self.assertEqual(len(res["pasos"]), 2)
        # Verifica que se hayan limpiado los prefijos numéricos de los pasos
        self.assertFalse(res["pasos"][0].startswith("1."))
        self.assertTrue(res["pasos"][0].startswith("Ubica el panel"))

    @patch.object(
        GeminiProviderService,
        'generar_contenido',
        return_value=json.dumps({
            "explicacion": "Para volver al listado de proyectos debes salir al Dashboard.",
            "pasos": [
                "1. Haz clic en el botón 'Volver al Dashboard' en la parte inferior del panel lateral."
            ],
            "componente_id": "btn-volver-dashboard",
            "requiere_cambio_vista": True,
            "vista_destino": "dashboard"
        })
    )
    def test_ayuda_pizarra_cambio_vista_dashboard(self, mock_gemini):
        from .services import AyudaAsistenteService
        res = AyudaAsistenteService.consultar_ayuda("¿Cómo vuelvo a mis proyectos?", "pizarra")
        self.assertEqual(res["componente_id"], "btn-volver-dashboard")
        self.assertTrue(res["requiere_cambio_vista"])
        self.assertEqual(res["vista_destino"], "dashboard")

    @patch.object(
        GeminiProviderService,
        'generar_contenido',
        return_value=json.dumps({
            "explicacion": "Para eliminar una entidad del diagrama, haz clic derecho sobre la figura para abrir el menú contextual y elige Eliminar.",
            "pasos": [
                "1. Haz clic derecho sobre la entidad en el lienzo.",
                "2. Selecciona la opción 'Eliminar' en el menú contextual que aparece."
            ],
            "componente_id": "entidad-lienzo",
            "requiere_cambio_vista": False,
            "vista_destino": None
        })
    )
    def test_ayuda_eliminar_entidad_ilumina_entidad_lienzo(self, mock_gemini):
        from .services import AyudaAsistenteService
        res = AyudaAsistenteService.consultar_ayuda("¿Cómo elimino una entidad?", "pizarra")
        self.assertEqual(res["componente_id"], "entidad-lienzo")
        self.assertFalse(res["requiere_cambio_vista"])
        self.assertEqual(len(res["pasos"]), 2)




