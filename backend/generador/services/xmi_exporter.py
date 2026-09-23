import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, Tuple
from modelado.models import Proyecto, Entidad, Atributo, Relacion

XMI_NS = 'http://schema.omg.org/spec/XMI/2.1'
UML_NS = 'http://schema.omg.org/spec/UML/2.1'

# Registro explícito de namespaces para evitar prefijos autogenerados como ns0:
ET.register_namespace('uml', UML_NS)
ET.register_namespace('xmi', XMI_NS)


class XMIExporter:
    """
    Exportador de diagramas de datos conceptuales a formato XML 2.1 (OMG UML / XMI 2.1)
    compatible con Enterprise Architect y herramientas estándar CASE.
    Genera únicamente la estructura estándar OMG (<uml:Model>) y omite extensiones propietarias.
    """

    TIPO_A_EAJAVA: Dict[str, str] = {
        Atributo.Tipo.STRING: 'EAJava_char',
        Atributo.Tipo.INTEGER: 'EAJava_int',
        Atributo.Tipo.LONG: 'EAJava_long',
        Atributo.Tipo.DOUBLE: 'EAJava_double',
        Atributo.Tipo.BOOLEAN: 'EAJava_boolean',
        Atributo.Tipo.DATE: 'EAJava_Date',
    }

    def __init__(self, proyecto: Proyecto):
        self.proyecto = proyecto

    def _generar_eaid(self, prefijo: str = "EAID") -> str:
        """Genera un identificador compatible con Enterprise Architect (EAID_HEX...)."""
        u = uuid.uuid4().hex.upper()
        # Formato: EAID_XXXXXXXX_XXXX_XXXX_XXXX_XXXXXXXXXXXX
        formatted = f"{u[:8]}_{u[8:12]}_{u[12:16]}_{u[16:20]}_{u[20:]}"
        return f"{prefijo}_{formatted}"

    def _generar_duid(self) -> str:
        """Genera un DUID hexadecimal de 8 caracteres para elementos de diagrama EA."""
        return uuid.uuid4().hex[:8].upper()

    def _es_cardinalidad_muchos(self, card_str: str) -> bool:
        """Devuelve True si la cardinalidad representa 'muchos' (*, 0..*, 1..*, etc.)."""
        c = (card_str or '').strip()
        if c in ('*', '0..*', '1..*'):
            return True
        if '..' in c and c.endswith('*'):
            return True
        return False


    def _parsear_cardinalidad(self, card_str: str) -> Tuple[int, int]:
        """
        Convierte una cardinalidad en string (ej. '1', '*', '0..1', '1..*', '0..*')
        a (lowerValue, upperValue) donde -1 representa infinito (*).
        """
        c = (card_str or '1').strip()
        if c == '1':
            return (1, 1)
        if c in ('*', '0..*'):
            return (0, -1)
        if c == '1..*':
            return (1, -1)
        if c == '0..1':
            return (0, 1)
        if '..' in c:
            partes = c.split('..')
            lower = int(partes[0]) if partes[0].isdigit() else 0
            upper = -1 if partes[1] == '*' else (int(partes[1]) if partes[1].isdigit() else 1)
            return (lower, upper)
        if c.isdigit():
            val = int(c)
            return (val, val)
        return (1, 1)

    def _crear_multiplicidad_elementos(
        self, parent: ET.Element, lower: int, upper: int
    ) -> None:
        """Agrega los elementos lowerValue y upperValue según la especificación OMG UML 2.1."""
        low_id = self._generar_eaid("EAID")
        ET.SubElement(parent, 'lowerValue', {
            f'{{{XMI_NS}}}type': 'uml:LiteralInteger',
            f'{{{XMI_NS}}}id': low_id,
            'value': str(lower),
        })

        upp_id = self._generar_eaid("EAID")
        if upper == -1:
            ET.SubElement(parent, 'upperValue', {
                f'{{{XMI_NS}}}type': 'uml:LiteralUnlimitedNatural',
                f'{{{XMI_NS}}}id': upp_id,
                'value': '-1',
            })
        else:
            ET.SubElement(parent, 'upperValue', {
                f'{{{XMI_NS}}}type': 'uml:LiteralInteger',
                f'{{{XMI_NS}}}id': upp_id,
                'value': str(upper),
            })

    def _agregar_atributos_a_clase(self, clase_elem: ET.Element, entidad: Entidad) -> None:
        """Agrega los ownedAttribute de una entidad a su elemento XML correspondiente."""
        for attr in entidad.atributos.all().order_by('orden', 'id'):
            attr_id = self._generar_eaid("EAID")
            attr_elem = ET.SubElement(clase_elem, 'ownedAttribute', {
                f'{{{XMI_NS}}}type': 'uml:Property',
                f'{{{XMI_NS}}}id': attr_id,
                'name': attr.nombre,
                'visibility': 'private',
                'isStatic': 'false',
                'isReadOnly': 'false',
                'isDerived': 'false',
                'isOrdered': 'false',
                'isUnique': 'true',
                'isDerivedUnion': 'false',
            })

            # Multiplicidad 1..1 para mantener el diagrama limpio en Enterprise Architect
            # (evita que EA renderice el sufijo '[0..1]' en el texto del diagrama para campos nulos)
            self._crear_multiplicidad_elementos(attr_elem, 1, 1)

            tipo_eajava = self.TIPO_A_EAJAVA.get(attr.tipo, 'EAJava_char')
            ET.SubElement(attr_elem, 'type', {
                f'{{{XMI_NS}}}idref': tipo_eajava,
            })

    def exportar_xml(self) -> str:
        """
        Construye y retorna el XML 2.1 estándar con extensión para Enterprise Architect.
        """
        # Raíz: <xmi:XMI>
        root = ET.Element(f'{{{XMI_NS}}}XMI', {
            f'{{{XMI_NS}}}version': '2.1',
        })

        # <xmi:Documentation>
        ET.SubElement(root, f'{{{XMI_NS}}}Documentation', {
            'exporter': 'Enterprise Architect',
            'exporterVersion': '6.5',
        })

        # <uml:Model xmi:type="uml:Model" name="EA_Model" visibility="public">
        model = ET.SubElement(root, f'{{{UML_NS}}}Model', {
            f'{{{XMI_NS}}}type': 'uml:Model',
            'name': 'EA_Model',
            'visibility': 'public',
        })

        # <packagedElement xmi:type="uml:Package" name="...">
        pkg_id = self._generar_eaid("EAPK")
        pkg = ET.SubElement(model, 'packagedElement', {
            f'{{{XMI_NS}}}type': 'uml:Package',
            f'{{{XMI_NS}}}id': pkg_id,
            'name': self.proyecto.nombre or 'Starter Class Diagram',
            'visibility': 'public',
        })

        # Mapeo de IDs de base de datos a EAIDs y local IDs para entidades
        entidad_eaid_map: Dict[int, str] = {}
        entidad_duid_map: Dict[int, str] = {}
        entidad_localid_map: Dict[int, str] = {}
        clase_elements_map: Dict[int, ET.Element] = {}

        entidades = list(self.proyecto.entidades.exclude(estado=Entidad.Estado.PAPELERA).prefetch_related('atributos'))

        # 1. Crear packagedElement para cada Entidad (Class o AssociationClass)
        for idx, entidad in enumerate(entidades):
            eaid = self._generar_eaid("EAID")
            entidad_eaid_map[entidad.id] = eaid
            entidad_duid_map[entidad.id] = self._generar_duid()
            entidad_localid_map[entidad.id] = str(idx + 1)

            tipo_uml = 'uml:AssociationClass' if entidad.es_intermedia else 'uml:Class'
            clase_elem = ET.SubElement(pkg, 'packagedElement', {
                f'{{{XMI_NS}}}type': tipo_uml,
                f'{{{XMI_NS}}}id': eaid,
                'name': entidad.nombre,
                'visibility': 'public',
            })
            clase_elements_map[entidad.id] = clase_elem

            # Si NO es intermedia, agregar sus atributos inmediatamente.
            # Para las clases intermedias (AssociationClass), los atributos se agregan
            # DESPUÉS de memberEnd y ownedEnd para respetar el orden estricto de Enterprise Architect.
            if not entidad.es_intermedia:
                self._agregar_atributos_a_clase(clase_elem, entidad)

        # 2. Procesar Relaciones
        relaciones = list(self.proyecto.relaciones.filter(
            entidad_origen_id__in=entidad_eaid_map.keys(),
            entidad_destino_id__in=entidad_eaid_map.keys()
        ).select_related('entidad_origen', 'entidad_destino', 'clase_asociacion'))

        assoc_class_to_conn_id: Dict[int, str] = {}
        entidades_intermedias_procesadas = set()
        connector_info_list: list = []

        # Filtrado defensivo: si una entidad intermedia ya tiene su relación N:M entre A y B,
        # ignorar únicamente las relaciones binarias directas residuales entre (intermedia, A) o (intermedia, B).
        # Cualquier relación legítima entre la entidad intermedia y otra tercera tabla C (o entre intermedias) debe conservarse.
        redundant_pairs = set()
        for rel in relaciones:
            if rel.clase_asociacion_id:
                t_id = rel.clase_asociacion_id
                a_id = rel.entidad_origen_id
                b_id = rel.entidad_destino_id
                redundant_pairs.add((t_id, a_id))
                redundant_pairs.add((a_id, t_id))
                redundant_pairs.add((t_id, b_id))
                redundant_pairs.add((b_id, t_id))

        # Aseguramos que las relaciones N:M con clase_asociacion se procesen primero,
        # de modo que las AssociationClasses configuren sus memberEnd/ownedEnd antes de recibir
        # otros extremos o ownedAttributes si se relacionan con otras clases.
        relaciones.sort(key=lambda r: 0 if r.clase_asociacion_id else 1)

        for rel in relaciones:
            # Si es una relación binaria residual redundante entre la intermedia y uno de sus padres N:M, omitir
            if not rel.clase_asociacion_id:
                if (rel.entidad_origen_id, rel.entidad_destino_id) in redundant_pairs:
                    continue

            origen_eaid = entidad_eaid_map[rel.entidad_origen_id]
            destino_eaid = entidad_eaid_map[rel.entidad_destino_id]

            if rel.tipo == Relacion.Tipo.HERENCIA:
                # La herencia en UML 2.1 se declara como <generalization> dentro de la clase hija (origen)
                hija_elem = clase_elements_map.get(rel.entidad_origen_id)
                gen_id = self._generar_eaid("EAID")
                if hija_elem is not None:
                    ET.SubElement(hija_elem, 'generalization', {
                        f'{{{XMI_NS}}}type': 'uml:Generalization',
                        f'{{{XMI_NS}}}id': gen_id,
                        'general': destino_eaid,
                    })
                connector_info_list.append({
                    'assoc_id': gen_id,
                    'nombre': rel.nombre_relacion or '',
                    'source_id': rel.entidad_origen_id,
                    'source_eaid': origen_eaid,
                    'source_nombre': rel.entidad_origen.nombre,
                    'target_id': rel.entidad_destino_id,
                    'target_eaid': destino_eaid,
                    'target_nombre': rel.entidad_destino.nombre,
                    'card_source': '',
                    'card_target': '',
                    'agg_source': 'none',
                    'agg_target': 'none',
                    'ea_type': 'Generalization',
                    'subtype': None,
                    'direction': 'Source -> Destination',
                    'assoc_class_eaid': None,
                })
            elif rel.clase_asociacion_id and rel.clase_asociacion_id in clase_elements_map:
                # Clase de Asociación (N:M): los ends se integran directamente en <uml:AssociationClass>
                assoc_elem = clase_elements_map[rel.clase_asociacion_id]
                assoc_id = entidad_eaid_map[rel.clase_asociacion_id]
                assoc_localid = entidad_localid_map.get(rel.clase_asociacion_id, '1')

                # GUID unificado para el conector y sus extremos
                conn_guid = uuid.uuid4().hex.upper()
                conn_id = f"EAID_{conn_guid[:8]}_{conn_guid[8:12]}_{conn_guid[12:16]}_{conn_guid[16:20]}_{conn_guid[20:]}"
                src_end_id = f"EAID_src{conn_guid[2:8]}_{conn_guid[8:12]}_{conn_guid[12:16]}_{conn_guid[16:20]}_{conn_guid[20:]}"
                dst_end_id = f"EAID_dst{conn_guid[2:8]}_{conn_guid[8:12]}_{conn_guid[12:16]}_{conn_guid[16:20]}_{conn_guid[20:]}"

                assoc_class_to_conn_id[rel.clase_asociacion_id] = conn_id
                entidades_intermedias_procesadas.add(rel.clase_asociacion_id)

                # Orden exacto Enterprise Architect / OMG UML 2.1:
                # 1. memberEnd destino
                ET.SubElement(assoc_elem, 'memberEnd', {f'{{{XMI_NS}}}idref': dst_end_id})
                # 2. memberEnd origen
                ET.SubElement(assoc_elem, 'memberEnd', {f'{{{XMI_NS}}}idref': src_end_id})
                # 3. ownedEnd origen (sin multiplicidad para evitar crear enlaces binarios en EA)
                src_end = ET.SubElement(assoc_elem, 'ownedEnd', {
                    f'{{{XMI_NS}}}type': 'uml:Property',
                    f'{{{XMI_NS}}}id': src_end_id,
                    'visibility': 'public',
                    'association': assoc_id,
                    'isStatic': 'false',
                    'isReadOnly': 'false',
                    'isDerived': 'false',
                    'isOrdered': 'false',
                    'isUnique': 'true',
                    'isDerivedUnion': 'false',
                    'aggregation': 'none',
                })
                ET.SubElement(src_end, 'type', {f'{{{XMI_NS}}}idref': origen_eaid})

                # 4. ownedEnd destino (sin multiplicidad para evitar crear enlaces binarios en EA)
                dst_end = ET.SubElement(assoc_elem, 'ownedEnd', {
                    f'{{{XMI_NS}}}type': 'uml:Property',
                    f'{{{XMI_NS}}}id': dst_end_id,
                    'visibility': 'public',
                    'association': assoc_id,
                    'isStatic': 'false',
                    'isReadOnly': 'false',
                    'isDerived': 'false',
                    'isOrdered': 'false',
                    'isUnique': 'true',
                    'isDerivedUnion': 'false',
                    'aggregation': 'none',
                })
                ET.SubElement(dst_end, 'type', {f'{{{XMI_NS}}}idref': destino_eaid})

                # 5. Atributos de la clase intermedia después de los ends
                intermedia_ent = next((e for e in entidades if e.id == rel.clase_asociacion_id), None)
                if intermedia_ent:
                    self._agregar_atributos_a_clase(assoc_elem, intermedia_ent)

                connector_info_list.append({
                    'assoc_id': conn_id,
                    'nombre': rel.nombre_relacion or '',
                    'source_id': rel.entidad_origen_id,
                    'source_eaid': origen_eaid,
                    'source_nombre': rel.entidad_origen.nombre,
                    'target_id': rel.entidad_destino_id,
                    'target_eaid': destino_eaid,
                    'target_nombre': rel.entidad_destino.nombre,
                    'card_source': '',
                    'card_target': '',
                    'agg_source': 'none',
                    'agg_target': 'none',
                    'ea_type': 'Association',
                    'subtype': 'Class',
                    'direction': 'Unspecified',
                    'assoc_class_eaid': assoc_id,
                    'assoc_class_localid': assoc_localid,
                })
            else:
                # Asociación, Agregación o Composición regular
                assoc_id = self._generar_eaid("EAID")
                src_end_id = self._generar_eaid("EAID")
                dst_end_id = self._generar_eaid("EAID")

                # En la pizarra y en el modelo conceptual:
                # - entidad_origen es donde inicia la conexión (la Parte / Source en EA)
                # - entidad_destino es donde termina y donde se dibuja el rombo (el Contenedor / Target en EA)
                assoc_attrs: Dict[str, str] = {
                    f'{{{XMI_NS}}}type': 'uml:Association',
                    f'{{{XMI_NS}}}id': assoc_id,
                    'visibility': 'public',
                }
                if rel.nombre_relacion:
                    assoc_attrs['name'] = rel.nombre_relacion

                assoc_elem = ET.SubElement(pkg, 'packagedElement', assoc_attrs)

                if rel.tipo in (Relacion.Tipo.AGREGACION, Relacion.Tipo.COMPOSICION):
                    agg_uml_tipo = 'composite' if rel.tipo == Relacion.Tipo.COMPOSICION else 'shared'
                    card_source = rel.cardinalidad_origen or '0..*'
                    card_target = rel.cardinalidad_destino or '1'

                    # Para Agregación y Composición, Enterprise Architect coloca el extremo destino
                    # como un <ownedAttribute> dentro de la clase origen (la parte):
                    source_class_elem = clase_elements_map.get(rel.entidad_origen_id)
                    lower_dest, upper_dest = self._parsear_cardinalidad(card_target)
                    if source_class_elem is not None:
                        dst_attr_attrs = {
                            f'{{{XMI_NS}}}type': 'uml:Property',
                            f'{{{XMI_NS}}}id': dst_end_id,
                            'visibility': 'public',
                            'association': assoc_id,
                            'isStatic': 'false',
                            'isReadOnly': 'false',
                            'isDerived': 'false',
                            'isOrdered': 'false',
                            'isUnique': 'true',
                            'isDerivedUnion': 'false',
                            'aggregation': 'none',
                        }
                        if rel.nombre_relacion:
                            dst_attr_attrs['name'] = rel.nombre_relacion
                        dst_attr = ET.SubElement(source_class_elem, 'ownedAttribute', dst_attr_attrs)
                        ET.SubElement(dst_attr, 'type', {f'{{{XMI_NS}}}idref': destino_eaid})
                        self._crear_multiplicidad_elementos(dst_attr, lower_dest, upper_dest)

                    # En la <uml:Association>, el primer memberEnd apunta al ownedAttribute de la clase origen
                    ET.SubElement(assoc_elem, 'memberEnd', {f'{{{XMI_NS}}}idref': dst_end_id})
                    # El segundo memberEnd apunta al ownedEnd de la asociación (la parte con aggregation composite/shared)
                    ET.SubElement(assoc_elem, 'memberEnd', {f'{{{XMI_NS}}}idref': src_end_id})

                    lower_orig, upper_orig = self._parsear_cardinalidad(card_source)
                    src_end_attrs = {
                        f'{{{XMI_NS}}}type': 'uml:Property',
                        f'{{{XMI_NS}}}id': src_end_id,
                        'visibility': 'public',
                        'association': assoc_id,
                        'isStatic': 'false',
                        'isReadOnly': 'false',
                        'isDerived': 'false',
                        'isOrdered': 'false',
                        'isUnique': 'true',
                        'isDerivedUnion': 'false',
                        'aggregation': agg_uml_tipo,
                    }
                    src_end = ET.SubElement(assoc_elem, 'ownedEnd', src_end_attrs)
                    ET.SubElement(src_end, 'type', {f'{{{XMI_NS}}}idref': origen_eaid})
                    self._crear_multiplicidad_elementos(src_end, lower_orig, upper_orig)

                    ea_type = 'Aggregation'
                    subtype = 'Strong' if rel.tipo == Relacion.Tipo.COMPOSICION else 'Shared'
                    direction = 'Source -> Destination'
                    agg_source = 'none'
                    agg_target = agg_uml_tipo
                else:
                    # Asociación regular: ambos extremos son ownedEnd dentro de la asociación
                    # Orden idéntico a Enterprise Architect: memberEnd[0] es destino, memberEnd[1] es origen
                    card_source = rel.cardinalidad_origen or '1'
                    card_target = rel.cardinalidad_destino or '1'

                    # memberEnd 1 y ownedEnd para destino
                    ET.SubElement(assoc_elem, 'memberEnd', {f'{{{XMI_NS}}}idref': dst_end_id})
                    lower_dest, upper_dest = self._parsear_cardinalidad(card_target)
                    dst_end_attrs = {
                        f'{{{XMI_NS}}}type': 'uml:Property',
                        f'{{{XMI_NS}}}id': dst_end_id,
                        'visibility': 'public',
                        'association': assoc_id,
                        'isStatic': 'false',
                        'isReadOnly': 'false',
                        'isDerived': 'false',
                        'isOrdered': 'false',
                        'isUnique': 'true',
                        'isDerivedUnion': 'false',
                        'aggregation': 'none',
                    }
                    if rel.nombre_relacion:
                        dst_end_attrs['name'] = rel.nombre_relacion
                    dst_end = ET.SubElement(assoc_elem, 'ownedEnd', dst_end_attrs)
                    ET.SubElement(dst_end, 'type', {f'{{{XMI_NS}}}idref': destino_eaid})
                    self._crear_multiplicidad_elementos(dst_end, lower_dest, upper_dest)

                    # memberEnd 2 y ownedEnd para origen
                    ET.SubElement(assoc_elem, 'memberEnd', {f'{{{XMI_NS}}}idref': src_end_id})
                    lower_orig, upper_orig = self._parsear_cardinalidad(card_source)
                    src_end_attrs = {
                        f'{{{XMI_NS}}}type': 'uml:Property',
                        f'{{{XMI_NS}}}id': src_end_id,
                        'visibility': 'public',
                        'association': assoc_id,
                        'isStatic': 'false',
                        'isReadOnly': 'false',
                        'isDerived': 'false',
                        'isOrdered': 'false',
                        'isUnique': 'true',
                        'isDerivedUnion': 'false',
                        'aggregation': 'none',
                    }
                    src_end = ET.SubElement(assoc_elem, 'ownedEnd', src_end_attrs)
                    ET.SubElement(src_end, 'type', {f'{{{XMI_NS}}}idref': origen_eaid})
                    self._crear_multiplicidad_elementos(src_end, lower_orig, upper_orig)

                    ea_type = 'Association'
                    subtype = None
                    direction = 'Unspecified'
                    agg_source = 'none'
                    agg_target = 'none'

                connector_info_list.append({
                    'assoc_id': assoc_id,
                    'nombre': rel.nombre_relacion or '',
                    'source_id': rel.entidad_origen_id,
                    'source_eaid': origen_eaid,
                    'source_nombre': rel.entidad_origen.nombre,
                    'target_id': rel.entidad_destino_id,
                    'target_eaid': destino_eaid,
                    'target_nombre': rel.entidad_destino.nombre,
                    'card_source': card_source,
                    'card_target': card_target,
                    'agg_source': agg_source,
                    'agg_target': agg_target,
                    'ea_type': ea_type,
                    'subtype': subtype,
                    'direction': direction,
                    'assoc_class_eaid': None,
                })

        # Si alguna entidad intermedia no fue procesada por una relación N:M, agregar sus atributos
        for entidad in entidades:
            if entidad.es_intermedia and entidad.id not in entidades_intermedias_procesadas:
                assoc_elem = clase_elements_map.get(entidad.id)
                if assoc_elem is not None:
                    self._agregar_atributos_a_clase(assoc_elem, entidad)

        # 3. Construir <xmi:Extension extender="Enterprise Architect" extenderID="6.5">
        extension = ET.SubElement(root, f'{{{XMI_NS}}}Extension', {
            'extender': 'Enterprise Architect',
            'extenderID': '6.5',
        })

        # 3.1 <elements>
        elements_elem = ET.SubElement(extension, 'elements')
        pkg_ext = ET.SubElement(elements_elem, 'element', {
            f'{{{XMI_NS}}}idref': pkg_id,
            f'{{{XMI_NS}}}type': 'uml:Package',
            'name': self.proyecto.nombre or 'Starter Class Diagram',
            'scope': 'public',
        })
        ET.SubElement(pkg_ext, 'model', {
            'package2': pkg_id,
            'tpos': '1',
            'ea_eleType': 'package',
        })
        ET.SubElement(pkg_ext, 'properties', {
            'isSpecification': 'false',
            'sType': 'Package',
            'nType': '0',
            'scope': 'public',
        })
        ET.SubElement(pkg_ext, 'project', {
            'author': 'DELL',
            'version': '1.0',
            'phase': '1.0',
            'complexity': '1',
            'status': 'Proposed',
        })

        for idx, entidad in enumerate(entidades):
            eaid = entidad_eaid_map[entidad.id]
            local_id = entidad_localid_map[entidad.id]
            is_assoc_class = entidad.es_intermedia and entidad.id in assoc_class_to_conn_id

            el_ext = ET.SubElement(elements_elem, 'element', {
                f'{{{XMI_NS}}}idref': eaid,
                f'{{{XMI_NS}}}type': 'uml:Class',
                'name': entidad.nombre,
                'scope': 'public',
            })
            ET.SubElement(el_ext, 'model', {
                'package': pkg_id,
                'tpos': '0',
                'ea_localid': local_id,
                'ea_eleType': 'element',
            })
            ET.SubElement(el_ext, 'properties', {
                'isSpecification': 'false',
                'sType': 'Class',
                'nType': '17' if is_assoc_class else '0',
                'scope': 'public',
                'isRoot': 'false',
                'isLeaf': 'false',
                'isAbstract': 'false',
                'isActive': 'false',
            })
            ET.SubElement(el_ext, 'project', {
                'author': 'DELL',
                'version': '1.0',
                'phase': '1.0',
                'complexity': '1',
                'status': 'Proposed',
            })
            ET.SubElement(el_ext, 'code', {'gentype': 'Java'})

            # extendedProperties: si es AssociationClass debe incluir conID apuntando al conector
            ext_props = {
                'tagged': '0',
                'package_name': self.proyecto.nombre or 'Starter Class Diagram',
            }
            if is_assoc_class:
                ext_props['conID'] = assoc_class_to_conn_id[entidad.id]
            ET.SubElement(el_ext, 'extendedProperties', ext_props)

            # <links> para Enterprise Architect:
            # Si la entidad tiene conectores (directos como origen o destino), se generan en <links>.
            # Para una AssociationClass sin relaciones externas, sus extremos N:M están entre A y B,
            # por lo que links_de_entidad estará vacío y no se generará el bloque <links> (idéntico a EA).
            links_de_entidad = [
                cinfo for cinfo in connector_info_list
                if cinfo.get('source_id') == entidad.id or cinfo.get('target_id') == entidad.id
            ]
            if links_de_entidad:
                links_elem = ET.SubElement(el_ext, 'links')
                for cinfo in links_de_entidad:
                    link_tag = cinfo['ea_type']  # 'Aggregation', 'Association', 'Generalization'
                    ET.SubElement(links_elem, link_tag, {
                        f'{{{XMI_NS}}}id': cinfo['assoc_id'],
                        'start': cinfo['source_eaid'],
                        'end': cinfo['target_eaid'],
                    })

        # 3.2 <connectors>
        connectors_elem = ET.SubElement(extension, 'connectors')
        for cinfo in connector_info_list:
            is_assoc_conn = bool(cinfo.get('assoc_class_eaid'))

            conn_attrs = {f'{{{XMI_NS}}}idref': cinfo['assoc_id']}
            if cinfo['nombre'] and not is_assoc_conn:
                conn_attrs['name'] = cinfo['nombre']
            conn_elem = ET.SubElement(connectors_elem, 'connector', conn_attrs)

            src_elem = ET.SubElement(conn_elem, 'source', {f'{{{XMI_NS}}}idref': cinfo['source_eaid']})
            ET.SubElement(src_elem, 'model', {'type': 'Class', 'name': cinfo['source_nombre']})
            ET.SubElement(src_elem, 'role', {'visibility': 'Public', 'targetScope': 'instance'})
            src_type_attrs = {'aggregation': cinfo['agg_source'], 'containment': 'Unspecified'}
            if cinfo['card_source'] and not is_assoc_conn:
                src_type_attrs['multiplicity'] = cinfo['card_source']
            ET.SubElement(src_elem, 'type', src_type_attrs)
            ET.SubElement(src_elem, 'modifiers', {
                'isOrdered': 'false',
                'changeable': 'none',
                'isNavigable': 'false',
            })

            dst_elem = ET.SubElement(conn_elem, 'target', {f'{{{XMI_NS}}}idref': cinfo['target_eaid']})
            ET.SubElement(dst_elem, 'model', {'type': 'Class', 'name': cinfo['target_nombre']})
            ET.SubElement(dst_elem, 'role', {'visibility': 'Public', 'targetScope': 'instance'})
            dst_type_attrs = {'aggregation': cinfo['agg_target'], 'containment': 'Unspecified'}
            if cinfo['card_target'] and not is_assoc_conn:
                dst_type_attrs['multiplicity'] = cinfo['card_target']
            ET.SubElement(dst_elem, 'type', dst_type_attrs)
            is_nav = 'true' if (not is_assoc_conn and (cinfo['ea_type'] == 'Aggregation' or cinfo['direction'] == 'Source -> Destination' or bool(cinfo.get('nombre')))) else 'false'
            ET.SubElement(dst_elem, 'modifiers', {
                'isOrdered': 'false',
                'changeable': 'none',
                'isNavigable': is_nav,
            })

            props_attrs = {'ea_type': cinfo['ea_type'], 'direction': cinfo['direction']}
            if cinfo['subtype']:
                props_attrs['subtype'] = cinfo['subtype']
            ET.SubElement(conn_elem, 'properties', props_attrs)

            labels_attrs = {}
            if not is_assoc_conn:
                if cinfo['card_source']:
                    labels_attrs['lb'] = cinfo['card_source']
                if cinfo['nombre']:
                    labels_attrs['mt'] = cinfo['nombre']
                if cinfo['card_target']:
                    labels_attrs['rb'] = cinfo['card_target']
            ET.SubElement(conn_elem, 'labels', labels_attrs)

            if is_assoc_conn:
                ET.SubElement(conn_elem, 'extendedProperties', {
                    'virtualInheritance': '0',
                    'associationclass': cinfo['assoc_class_eaid'],
                    'privatedata1': cinfo.get('assoc_class_localid', '1'),
                })

        # 3.3 <primitivetypes>
        pt_elem = ET.SubElement(extension, 'primitivetypes')
        pt_pkg = ET.SubElement(pt_elem, 'packagedElement', {
            f'{{{XMI_NS}}}type': 'uml:Package',
            f'{{{XMI_NS}}}id': 'EAPrimitiveTypesPackage',
            'name': 'EA_PrimitiveTypes_Package',
            'visibility': 'public',
        })
        java_pkg = ET.SubElement(pt_pkg, 'packagedElement', {
            f'{{{XMI_NS}}}type': 'uml:Package',
            f'{{{XMI_NS}}}id': 'EAJavaTypesPackage',
            'name': 'EA_Java_Types_Package',
            'visibility': 'public',
        })
        tipos_primitivos = [
            ('EAJava_char', 'char', 'String'),
            ('EAJava_int', 'int', 'Integer'),
            ('EAJava_Date', 'Date', None),
            ('EAJava_long', 'long', None),
            ('EAJava_double', 'double', None),
            ('EAJava_boolean', 'boolean', 'Boolean'),
        ]
        for tid, tname, gen_href in tipos_primitivos:
            prim_elem = ET.SubElement(java_pkg, 'packagedElement', {
                f'{{{XMI_NS}}}type': 'uml:PrimitiveType',
                f'{{{XMI_NS}}}id': tid,
                'name': tname,
                'visibility': 'public',
            })
            if gen_href:
                gen_el = ET.SubElement(prim_elem, 'generalization', {
                    f'{{{XMI_NS}}}type': 'uml:Generalization',
                    f'{{{XMI_NS}}}id': f'{tid}_General',
                })
                ET.SubElement(gen_el, 'general', {
                    'href': f'http://schema.omg.org/spec/UML/2.1/uml.xml#{gen_href}',
                })

        # 3.4 <profiles/>
        ET.SubElement(extension, 'profiles')

        # 3.5 <diagrams>
        diagrams_elem = ET.SubElement(extension, 'diagrams')
        diag_id = self._generar_eaid("EAID")
        diag_elem = ET.SubElement(diagrams_elem, 'diagram', {
            f'{{{XMI_NS}}}id': diag_id,
        })
        ET.SubElement(diag_elem, 'model', {
            'package': pkg_id,
            'localID': '1',
            'owner': pkg_id,
        })
        ET.SubElement(diag_elem, 'properties', {
            'name': self.proyecto.nombre or 'Starter Class Diagram',
            'type': 'Logical',
        })
        ET.SubElement(diag_elem, 'project', {
            'author': 'DELL',
            'version': '1.0',
        })
        diag_elements = ET.SubElement(diag_elem, 'elements')

        # Normalización de coordenadas para Enterprise Architect:
        # En la pizarra virtual el lienzo es infinito y el usuario puede mover entidades
        # hacia cuadrantes negativos o muy distantes. Calculamos un desplazamiento uniforme (shift)
        # para que la entidad más a la izquierda y la más arriba comiencen en MARGIN (50px),
        # preservando exactamente las distancias relativas entre todas las tablas.
        MARGIN = 50
        coords_x = [entidad.coord_x for entidad in entidades if entidad.coord_x is not None]
        coords_y = [entidad.coord_y for entidad in entidades if entidad.coord_y is not None]

        min_x = min(coords_x) if coords_x else None
        min_y = min(coords_y) if coords_y else None

        shift_x = int(MARGIN - min_x) if min_x is not None else 0
        shift_y = int(MARGIN - min_y) if min_y is not None else 0

        for i, entidad in enumerate(entidades):
            eaid = entidad_eaid_map[entidad.id]
            duid = entidad_duid_map[entidad.id]
            if entidad.coord_x is not None:
                left = max(MARGIN, int(entidad.coord_x + shift_x))
            else:
                left = MARGIN + (i % 3) * 260

            if entidad.coord_y is not None:
                top = max(MARGIN, int(entidad.coord_y + shift_y))
            else:
                top = MARGIN + (i // 3) * 200

            w = int(entidad.ancho) if (entidad.ancho is not None and entidad.ancho > 0) else 180
            h = 40 + max(len(entidad.atributos.all()), 1) * 20
            right = left + w
            bottom = top + h
            ET.SubElement(diag_elements, 'element', {
                'geometry': f'Left={left};Top={top};Right={right};Bottom={bottom};',
                'subject': eaid,
                'seqno': str(i + 1),
                'style': f'DUID={duid};',
            })
        for cinfo in connector_info_list:
            soid = entidad_duid_map.get(cinfo.get('source_id'), '')
            eoid = entidad_duid_map.get(cinfo.get('target_id'), '')
            if soid and eoid:
                c_style = f'Mode=3;EOID={eoid};SOID={soid};Color=-1;LWidth=0;Hidden=0;'
            else:
                c_style = 'Mode=3;Color=-1;LWidth=0;Hidden=0;'
            ET.SubElement(diag_elements, 'element', {
                'subject': cinfo['assoc_id'],
                'style': c_style,
            })

        # Indentación estándar y exportación a string
        ET.indent(root, space='\t')
        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        return xml_bytes.decode('utf-8')
