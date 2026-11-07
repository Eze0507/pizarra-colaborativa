"""Prueba externa opcional; solo se activa con NODOBOARD_FINANZAS_XMI."""
import os
from pathlib import Path
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.test import TestCase

from generador.services.xmi_importer import XMIImporter
from generador.services.spring_contract import capture_generation_contract
from generador.services.spring_generator import generate_spring_boot_base
from generador.services.xmi_importer import (
    parse_legacy_fk_attribute_name,
    prepare_imported_persistence,
    remove_hidden_duplicate_classifiers,
    resolve_legacy_fk_name_collisions,
)
from .models import Atributo, Entidad, Proyecto
from .validation import validate_project


class LegacyForeignKeyNameTests(TestCase):
    def test_parses_enterprise_architect_fk_annotation(self):
        self.assertEqual(
            parse_legacy_fk_attribute_name('created_by(FK; auth_user)'),
            ('created_by', 'auth_user'),
        )
        self.assertEqual(
            parse_legacy_fk_attribute_name('deleted_by(FK; auth_user)}'),
            ('deleted_by', 'auth_user'),
        )

    def test_preserves_names_without_legacy_annotation(self):
        self.assertEqual(
            parse_legacy_fk_attribute_name('created_at'),
            ('created_at', None),
        )

    def test_resolves_collision_without_guessing_fk_semantics(self):
        attributes = [
            {'nombre': 'deleted_at', 'fk_target_name': None},
            {'nombre': 'deleted_at', 'fk_target_name': 'auth_user'},
        ]
        resolve_legacy_fk_name_collisions(attributes)
        self.assertEqual(
            [item['nombre'] for item in attributes],
            ['deleted_at', 'deleted_at_auth_user'],
        )


class ImportedPersistencePolicyTests(TestCase):
    @staticmethod
    def classifier(name, attributes, *, kind='clase', abstract=False):
        return {
            'nombre': name,
            'tipo_clasificador': kind,
            'abstracto': abstract,
            'atributos': attributes,
        }

    @staticmethod
    def attribute(name, type_name='long', *, key=False):
        return {
            'nombre': name,
            'tipo': type_name,
            'es_clave': key,
            'es_nulo': True,
        }

    def test_infers_single_supported_id_for_concrete_class(self):
        raw = {'c1': self.classifier('Producto', [self.attribute('id')])}

        metrics = prepare_imported_persistence(raw)

        self.assertEqual(
            raw['c1']['tipo_clasificador'],
            Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        self.assertTrue(raw['c1']['atributos'][0]['es_clave'])
        self.assertFalse(raw['c1']['atributos'][0]['es_nulo'])
        self.assertEqual(metrics['claves_id_inferidas'], 1)

    def test_prefers_explicit_or_preserved_key_without_guessing_ambiguity(self):
        explicit = self.classifier('Factura', [self.attribute('codigo', key=True)])
        preserved = self.classifier('Cliente', [self.attribute('uuid', 'string')])
        ambiguous = self.classifier(
            'Ambigua',
            [self.attribute('id'), self.attribute('ID')],
        )
        raw = {'c1': explicit, 'c2': preserved, 'c3': ambiguous}

        metrics = prepare_imported_persistence(raw, {'cliente': 'uuid'})

        self.assertEqual(metrics['claves_explicitamente_importadas'], 1)
        self.assertEqual(metrics['claves_preservadas'], 1)
        self.assertEqual(metrics['claves_id_inferidas'], 0)
        self.assertEqual(
            preserved['tipo_clasificador'],
            Entidad.TipoClasificador.ENTIDAD_PERSISTENTE,
        )
        self.assertEqual(
            ambiguous['tipo_clasificador'],
            Entidad.TipoClasificador.CLASE,
        )

    def test_excludes_interface_abstract_class_and_unsupported_key(self):
        raw = {
            'i': self.classifier(
                'Contrato', [self.attribute('id')],
                kind=Entidad.TipoClasificador.INTERFAZ,
            ),
            'a': self.classifier('Base', [self.attribute('id')], abstract=True),
            'd': self.classifier(
                'Temporal', [self.attribute('id', Atributo.Tipo.DATE)]
            ),
        }

        metrics = prepare_imported_persistence(raw)

        self.assertEqual(metrics['entidades_persistentes'], 0)
        self.assertEqual(metrics['entidades_no_elegibles_persistencia'], 3)


class HiddenDuplicateClassifierTests(TestCase):
    @staticmethod
    def classifier(name, *, attribute='id'):
        return {
            'nombre': name,
            'es_intermedia': False,
            'tipo_clasificador': Entidad.TipoClasificador.CLASE,
            'abstracto': False,
            'atributos': [{
                'nombre': attribute, 'tipo': Atributo.Tipo.LONG,
                'tipo_ref_eaid': None, 'visibilidad': 'private',
                'es_estatico': False, 'valor_predeterminado': '',
                'es_nulo': False, 'es_clave': True,
            }],
            'operaciones': [],
        }

    def test_omits_identical_hidden_unreferenced_copy(self):
        raw = {
            'hidden': self.classifier('users_sucursal'),
            'visible': self.classifier('users_sucursal'),
            'sucursal': self.classifier('sucursal'),
        }
        associations = {
            'a1': {
                'is_assoc_class': False,
                'ends': [{'class_id': 'visible'}, {'class_id': 'sucursal'}],
            }
        }

        omitted = remove_hidden_duplicate_classifiers(
            raw, associations, [], [], {'visible': {'x': 10, 'y': 20, 'w': 200}}
        )

        self.assertEqual(omitted, 1)
        self.assertNotIn('hidden', raw)
        self.assertIn('visible', raw)

    def test_preserves_ambiguous_or_structurally_different_duplicates(self):
        both_visible = {
            'one': self.classifier('Cliente'),
            'two': self.classifier('Cliente'),
        }
        different = {
            'one': self.classifier('Pedido'),
            'two': self.classifier('Pedido', attribute='codigo'),
        }

        self.assertEqual(remove_hidden_duplicate_classifiers(
            both_visible, {}, [], [], {
                'one': {'x': 0, 'y': 0, 'w': 200},
                'two': {'x': 300, 'y': 0, 'w': 200},
            }
        ), 0)
        self.assertEqual(remove_hidden_duplicate_classifiers(
            different, {}, [], [], {'one': {'x': 0, 'y': 0, 'w': 200}}
        ), 0)
        self.assertEqual(len(both_visible), 2)
        self.assertEqual(len(different), 2)


@skipUnless(os.environ.get("NODOBOARD_FINANZAS_XMI"), "XMI externo no configurado")
class FinanzasXMICompatibilityTest(TestCase):
    def test_import_and_validate_external_fixture_in_ephemeral_database(self):
        path = Path(os.environ["NODOBOARD_FINANZAS_XMI"])
        raw = path.read_bytes()
        xml = raw.decode("windows-1252")
        self.assertIn("20131001", xml)

        owner = get_user_model().objects.create_user(username="finanzas-xmi-test")
        project = Proyecto.objects.create(propietario=owner, nombre="Finanzas XMI efimero")
        result = XMIImporter(project).importar_xml(xml, reemplazar_existente=True)
        self.assertIsInstance(result, dict)
        self.assertGreater(project.entidades.count(), 0)
        self.assertEqual(result["atributos_fk_normalizados"], 51)
        self.assertEqual(
            project.entidades.filter(
                tipo_clasificador=Entidad.TipoClasificador.ENTIDAD_PERSISTENTE
            ).count(),
            13,
        )
        self.assertEqual(
            Atributo.objects.filter(
                entidad__proyecto=project,
                es_clave=True,
            ).count(),
            13,
        )
        self.assertEqual(result['entidades_persistentes'], 13)
        self.assertEqual(result['claves_id_inferidas'], 13)

        report = {}
        for profile in ("uml", "java", "jpa"):
            validation = validate_project(project, profile)
            self.assertEqual(validation["perfil"], profile)
            self.assertEqual(validation["origen"], "orm")
            report[profile] = {
                "resumen": validation["resumen"],
                "codigos": sorted({item["codigo"] for item in validation["hallazgos"]}),
            }
            self.assertNotIn("JAVA_INVALID_IDENTIFIER", report[profile]["codigos"])
            self.assertEqual(
                validation["resumen"]["errores"],
                0,
                [item for item in validation["hallazgos"] if item["severidad"] == "error"],
            )

        options = {
            'modelo': True,
            'repositorio': True,
            'servicio': True,
            'controlador': True,
        }
        capture = capture_generation_contract(
            project_id=project.id,
            expected_revision=project.revision,
            user=owner,
            model_enabled=True,
            crud_enabled=True,
        )
        generated = generate_spring_boot_base(
            capture,
            project_name='finanzas',
            base_package='com.example.finanzas',
            options=options,
        )
        self.assertEqual(
            sum('/repository/' in name for name in generated.files),
            13,
        )
        self.assertEqual(
            sum('/service/' in name for name in generated.files),
            13,
        )
        self.assertEqual(
            sum('/controller/' in name for name in generated.files),
            13,
        )

        print("FINANZAS_XMI_VALIDATION", report)
