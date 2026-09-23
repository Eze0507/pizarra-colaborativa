import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction
from modelado.models import Proyecto, Entidad, Atributo, Relacion

XMI_NS = 'http://schema.omg.org/spec/XMI/2.1'
UML_NS = 'http://schema.omg.org/spec/UML/2.1'


class XMIImporter:
    """
    Importador de diagramas de datos conceptuales a partir de archivos XML 2.1 (OMG UML / XMI 2.1)
    generados por Enterprise Architect u otras herramientas CASE estándar.
    Ignora por completo las extensiones propietarias (<xmi:Extension>) y procesa recursivamente
    todos los paquetes para extraer Clases, Clases de Asociación, Atributos y Relaciones.
    """

    def __init__(self, proyecto: Proyecto):
        self.proyecto = proyecto

    def _obtener_attr(self, elem: ET.Element, name: str) -> Optional[str]:
        """Obtiene un atributo buscando con y sin namespaces."""
        if name in elem.attrib:
            return elem.attrib[name]
        # Probar con namespace XMI
        xmi_key = f'{{{XMI_NS}}}{name}'
        if xmi_key in elem.attrib:
            return elem.attrib[xmi_key]
        # Probar con namespace UML
        uml_key = f'{{{UML_NS}}}{name}'
        if uml_key in elem.attrib:
            return elem.attrib[uml_key]
        # Probar con prefijo xmi:
        if f'xmi:{name}' in elem.attrib:
            return elem.attrib[f'xmi:{name}']
        # Probar buscando cualquier sufijo
        for k, v in elem.attrib.items():
            if k.endswith(f'}}{name}') or k.endswith(f':{name}'):
                return v
        return None

    def _limpiar_tag(self, elem: ET.Element) -> str:
        """Devuelve el tag local sin namespace."""
        tag = elem.tag
        if '}' in tag:
            return tag.split('}', 1)[1]
        if ':' in tag:
            return tag.split(':', 1)[1]
        return tag

    def _mapear_tipo_dato(self, tipo_raw: Optional[str]) -> str:
        """Mapea tipos de Enterprise Architect o tipos primitivos a Atributo.Tipo."""
        if not tipo_raw:
            return Atributo.Tipo.STRING

        t = tipo_raw.lower()
        if 'int' in t or 'serial' in t:
            return Atributo.Tipo.INTEGER
        if 'long' in t or 'bigint' in t:
            return Atributo.Tipo.LONG
        if any(x in t for x in ('float', 'double', 'decimal', 'real', 'numeric')):
            return Atributo.Tipo.DOUBLE
        if any(x in t for x in ('bool', 'boolean')):
            return Atributo.Tipo.BOOLEAN
        if any(x in t for x in ('date', 'time', 'timestamp')):
            return Atributo.Tipo.DATE

        return Atributo.Tipo.STRING

    def _formatear_cardinalidad(self, lower: Optional[str], upper: Optional[str]) -> str:
        """Calcula el string de cardinalidad UML a partir de lowerValue y upperValue."""
        l_val = (lower or '').strip()
        u_val = (upper or '').strip()

        # Defaults UML cuando no se especifican
        if not l_val and not u_val:
            return '1'

        u_is_unlimited = (u_val in ('*', '-1'))
        u_num = -1 if u_is_unlimited else (int(u_val) if u_val.isdigit() else 1)
        # Si u_is_unlimited y no se especificó lowerValue, el default estándar en modelado de datos es 0
        l_num = int(l_val) if l_val.lstrip('-').isdigit() else (0 if u_is_unlimited else 1)

        if l_num == 1 and u_num == 1:
            return '1'
        if l_num == 0 and u_num == 1:
            return '0..1'
        if l_num == 0 and u_num == -1:
            return '0..*'
        if l_num == 1 and u_num == -1:
            return '1..*'
        if l_num == u_num and u_num > 0:
            return str(l_num)
        if u_num == -1:
            return f"{l_num}..*"
        return f"{l_num}..{u_num}"

    def _calcular_puertos_relacion(
        self,
        origen_ent: Entidad,
        destino_ent: Entidad,
        uso_puertos: Dict[int, Dict[str, int]]
    ) -> Tuple[str, str]:
        """
        Determina puertos óptimos (top, bottom, left, right) basados en la posición
        relativa de las dos entidades en la cuadrícula del lienzo, distribuyendo
        las conexiones para evitar colisiones.
        """
        puertos_por_lado = {
            'top': ['top-1', 'top-0', 'top-2'],
            'bottom': ['bottom-1', 'bottom-0', 'bottom-2'],
            'left': ['left-1', 'left-2', 'left-0', 'left-3'],
            'right': ['right-1', 'right-2', 'right-0', 'right-3'],
        }

        if origen_ent.id not in uso_puertos:
            uso_puertos[origen_ent.id] = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}
        if destino_ent.id not in uso_puertos:
            uso_puertos[destino_ent.id] = {'top': 0, 'bottom': 0, 'left': 0, 'right': 0}

        # Caso autoreferencia
        if origen_ent.id == destino_ent.id:
            idx_orig = uso_puertos[origen_ent.id]['top'] % 3
            idx_dest = uso_puertos[origen_ent.id]['right'] % 4
            uso_puertos[origen_ent.id]['top'] += 1
            uso_puertos[origen_ent.id]['right'] += 1
            return (puertos_por_lado['top'][idx_orig], puertos_por_lado['right'][idx_dest])

        cx1 = origen_ent.coord_x + 110.0
        cy1 = origen_ent.coord_y + 90.0
        cx2 = destino_ent.coord_x + 110.0
        cy2 = destino_ent.coord_y + 90.0

        dx = cx2 - cx1
        dy = cy2 - cy1

        if abs(dx) >= abs(dy):
            if dx >= 0:
                lado_orig, lado_dest = 'right', 'left'
            else:
                lado_orig, lado_dest = 'left', 'right'
        else:
            if dy >= 0:
                lado_orig, lado_dest = 'bottom', 'top'
            else:
                lado_orig, lado_dest = 'top', 'bottom'

        opciones_orig = puertos_por_lado[lado_orig]
        opciones_dest = puertos_por_lado[lado_dest]

        p_orig = opciones_orig[uso_puertos[origen_ent.id][lado_orig] % len(opciones_orig)]
        uso_puertos[origen_ent.id][lado_orig] += 1

        p_dest = opciones_dest[uso_puertos[destino_ent.id][lado_dest] % len(opciones_dest)]
        uso_puertos[destino_ent.id][lado_dest] += 1

        return (p_orig, p_dest)

    def importar_xml(self, contenido_xml: str, reemplazar_existente: bool = True) -> Dict[str, Any]:
        """
        Parsea el contenido XML e inserta las entidades, atributos y relaciones en la base de datos.
        """
        # Limpieza básica y parseo del XML
        if isinstance(contenido_xml, bytes):
            contenido_xml = contenido_xml.decode('utf-8', errors='replace')

        root = ET.fromstring(contenido_xml)

        # 1. Localizar el contenedor <uml:Model> de forma insensible a namespaces
        model_node = None
        for child in root.iter():
            if self._limpiar_tag(child) == 'Model':
                model_node = child
                break

        if model_node is None:
            # Si no hay tag Model explícito, usar root
            model_node = root

        # 2. Recolección de Clases, Clases de Asociación, Generalizaciones y Asociaciones
        # Se recorre recursivamente todo el árbol bajo el modelo, ignorando <xmi:Extension>
        raw_classes: Dict[str, Dict[str, Any]] = {}
        raw_associations: Dict[str, Dict[str, Any]] = {}
        generalizations: List[Tuple[str, str]] = []  # (subclass_eaid, superclass_eaid)

        # Mapa auxiliar de ends de asociación que estén embebidos como ownedAttribute en clases
        association_ends_by_assoc: Dict[str, List[Dict[str, Any]]] = {}

        for elem in model_node.iter():
            # Ignorar extensiones propietarias
            if self._limpiar_tag(elem) == 'Extension' or elem.attrib.get('extender') == 'Enterprise Architect':
                continue

            elem_type = self._obtener_attr(elem, 'type') or ''
            elem_id = self._obtener_attr(elem, 'id')
            elem_name = elem.attrib.get('name')

            # --- A. CLASES Y CLASES DE ASOCIACIÓN ---
            if elem_type in ('uml:Class', 'Class', 'uml:AssociationClass', 'AssociationClass') and elem_id:
                is_assoc_class = 'AssociationClass' in elem_type
                attrs_list: List[Dict[str, Any]] = []

                # Buscar atributos y generalizaciones directas de esta clase
                for child in elem:
                    child_tag = self._limpiar_tag(child)

                    # Generalización (Herencia)
                    if child_tag == 'generalization' or self._obtener_attr(child, 'type') in ('uml:Generalization', 'Generalization'):
                        gen_target = child.attrib.get('general')
                        if not gen_target:
                            for gen_child in child:
                                if self._limpiar_tag(gen_child) == 'general':
                                    gen_target = self._obtener_attr(gen_child, 'idref') or gen_child.attrib.get('href')
                        if gen_target:
                            generalizations.append((elem_id, gen_target))

                    # ownedAttribute
                    elif child_tag == 'ownedAttribute':
                        attr_name = child.attrib.get('name')
                        attr_assoc = child.attrib.get('association')

                        # Si tiene 'association', es un extremo navegable de una asociación externa
                        if attr_assoc:
                            target_class_id = None
                            for t_child in child:
                                if self._limpiar_tag(t_child) == 'type':
                                    target_class_id = self._obtener_attr(t_child, 'idref') or t_child.attrib.get('type')
                            if not target_class_id:
                                target_class_id = self._obtener_attr(child, 'type')

                            lower_v = None
                            upper_v = None
                            for v_child in child:
                                v_tag = self._limpiar_tag(v_child)
                                if v_tag == 'lowerValue':
                                    lower_v = v_child.attrib.get('value')
                                elif v_tag == 'upperValue':
                                    upper_v = v_child.attrib.get('value')

                            end_info = {
                                'class_id': target_class_id or elem_id,
                                'aggregation': child.attrib.get('aggregation', 'none'),
                                'lower': lower_v,
                                'upper': upper_v,
                            }
                            association_ends_by_assoc.setdefault(attr_assoc, []).append(end_info)

                        # Si tiene nombre real de columna, es un atributo de la entidad
                        if attr_name:
                            # Determinar tipo
                            tipo_str = None
                            for t_child in child:
                                if self._limpiar_tag(t_child) == 'type':
                                    tipo_str = self._obtener_attr(t_child, 'idref') or t_child.attrib.get('name')
                            if not tipo_str:
                                tipo_str = self._obtener_attr(child, 'type')

                            # Multiplicidad (nulabilidad)
                            lower_val = '1'
                            for v_child in child:
                                if self._limpiar_tag(v_child) == 'lowerValue':
                                    lower_val = v_child.attrib.get('value', '1')

                            es_nulo = (lower_val == '0')

                            # Detección de clave primaria
                            nombre_lower = attr_name.lower().strip()
                            es_clave = (
                                nombre_lower == 'id' or
                                nombre_lower.startswith('id_') or
                                nombre_lower.endswith('_id') or
                                nombre_lower in ('pk', 'codigo')
                            )

                            attrs_list.append({
                                'nombre': attr_name,
                                'tipo': self._mapear_tipo_dato(tipo_str),
                                'es_nulo': es_nulo,
                                'es_clave': es_clave,
                            })

                raw_classes[elem_id] = {
                    'nombre': elem_name or f"Entidad_{elem_id[-6:]}",
                    'es_intermedia': is_assoc_class,
                    'atributos': attrs_list,
                }

                # Si es AssociationClass, registrarla también como asociación
                if is_assoc_class:
                    raw_associations[elem_id] = {
                        'name': elem_name,
                        'is_assoc_class': True,
                        'ends': [],
                    }

            # --- B. ASOCIACIONES ---
            elif elem_type in ('uml:Association', 'Association') and elem_id:
                raw_associations[elem_id] = {
                    'name': elem_name,
                    'is_assoc_class': False,
                    'ends': [],
                }

        # 3. Extraer ownedEnds directos de cada asociación
        for elem in model_node.iter():
            if self._limpiar_tag(elem) == 'Extension' or elem.attrib.get('extender') == 'Enterprise Architect':
                continue

            elem_id = self._obtener_attr(elem, 'id')
            if elem_id in raw_associations:
                for child in elem:
                    if self._limpiar_tag(child) == 'ownedEnd':
                        target_class_id = None
                        for t_child in child:
                            if self._limpiar_tag(t_child) == 'type':
                                target_class_id = self._obtener_attr(t_child, 'idref') or t_child.attrib.get('type')
                        if not target_class_id:
                            target_class_id = self._obtener_attr(child, 'type')

                        lower_v = None
                        upper_v = None
                        for v_child in child:
                            v_tag = self._limpiar_tag(v_child)
                            if v_tag == 'lowerValue':
                                lower_v = v_child.attrib.get('value')
                            elif v_tag == 'upperValue':
                                upper_v = v_child.attrib.get('value')

                        raw_associations[elem_id]['ends'].append({
                            'class_id': target_class_id,
                            'aggregation': child.attrib.get('aggregation', 'none'),
                            'lower': lower_v,
                            'upper': upper_v,
                        })

        # Fusionar extremos externos hallados en ownedAttribute
        for assoc_id, extra_ends in association_ends_by_assoc.items():
            if assoc_id in raw_associations:
                raw_associations[assoc_id]['ends'].extend(extra_ends)

        # =========================================================================
        # PROCESAMIENTO EN DOS PASADAS (TWO-PASS PARSING)
        # =========================================================================
        with transaction.atomic():
            if reemplazar_existente:
                self.proyecto.relaciones.all().delete()
                self.proyecto.entidades.all().delete()

            eaid_to_entidad: Dict[str, Entidad] = {}
            entidades_creadas = 0
            atributos_creados = 0
            relaciones_creadas = 0
            relaciones_creadas_objs: List[Relacion] = []

            # ---------------------------------------------------------------------
            # PASADA 1: Creación de Entidades y Atributos (Classes y AssociationClasses)
            # ---------------------------------------------------------------------
            cols = 3
            for idx, (eaid, class_data) in enumerate(raw_classes.items()):
                row = idx // cols
                col = idx % cols
                coord_x = 80.0 + col * 340.0
                coord_y = 80.0 + row * 260.0

                entidad = Entidad.objects.create(
                    proyecto=self.proyecto,
                    nombre=class_data['nombre'],
                    estado=Entidad.Estado.ACTIVO,
                    coord_x=coord_x,
                    coord_y=coord_y,
                    ancho=220.0,
                    es_intermedia=class_data['es_intermedia'],
                )
                eaid_to_entidad[eaid] = entidad
                entidades_creadas += 1

                for orden, attr_data in enumerate(class_data['atributos']):
                    Atributo.objects.create(
                        entidad=entidad,
                        nombre=attr_data['nombre'],
                        tipo=attr_data['tipo'],
                        es_clave=attr_data['es_clave'],
                        es_nulo=attr_data['es_nulo'],
                        orden=orden,
                    )
                    atributos_creados += 1

            # ---------------------------------------------------------------------
            # PASADA 2: Creación de Relaciones (uml:Association, AssociationClass y Herencia)
            # ---------------------------------------------------------------------
            uso_puertos: Dict[int, Dict[str, int]] = {}

            # A. Relaciones estándar y clases de asociación
            for assoc_id, assoc_data in raw_associations.items():
                ends = [e for e in assoc_data['ends'] if e.get('class_id') in eaid_to_entidad]
                if len(ends) >= 2:
                    end_a = ends[0]
                    end_b = ends[1]

                    # Si es AssociationClass, vincular la entidad intermedia
                    ent_intermedia = None
                    if assoc_data.get('is_assoc_class') and assoc_id in eaid_to_entidad:
                        ent_intermedia = eaid_to_entidad[assoc_id]

                    # Determinar tipo según agregación
                    tipo_rel = Relacion.Tipo.ASOCIACION
                    if end_a.get('aggregation') == 'composite' or end_b.get('aggregation') == 'composite':
                        tipo_rel = Relacion.Tipo.COMPOSICION
                    elif end_a.get('aggregation') == 'shared' or end_b.get('aggregation') == 'shared':
                        tipo_rel = Relacion.Tipo.AGREGACION

                    # En la pizarra (JointJS), el rombo de composición/agregación se dibuja en entidad_destino (el contenedor).
                    # En el XML de Enterprise Architect, el extremo con aggregation='composite'/'shared' representa
                    # la parte contenida (hijo/source/origen), mientras que el extremo opuesto es el contenedor (padre/target/destino).
                    if tipo_rel in (Relacion.Tipo.COMPOSICION, Relacion.Tipo.AGREGACION):
                        if end_a.get('aggregation') in ('composite', 'shared'):
                            end_orig = end_a
                            end_dest = end_b
                        elif end_b.get('aggregation') in ('composite', 'shared'):
                            end_orig = end_b
                            end_dest = end_a
                        else:
                            card_a = self._formatear_cardinalidad(end_a.get('lower'), end_a.get('upper'))
                            card_b = self._formatear_cardinalidad(end_b.get('lower'), end_b.get('upper'))
                            if card_a in ('0..*', '*', '1..*') and card_b in ('1', '0..1'):
                                end_orig = end_a
                                end_dest = end_b
                            else:
                                end_orig = end_b
                                end_dest = end_a
                    else:
                        end_orig = end_a
                        end_dest = end_b

                    origen_ent = eaid_to_entidad[end_orig['class_id']]
                    destino_ent = eaid_to_entidad[end_dest['class_id']]

                    card_orig = self._formatear_cardinalidad(end_orig.get('lower'), end_orig.get('upper'))
                    card_dest = self._formatear_cardinalidad(end_dest.get('lower'), end_dest.get('upper'))

                    # Para clases de asociación N:M sin multiplicidad explícita, default UML a 0..*
                    if ent_intermedia:
                        if not end_orig.get('lower') and not end_orig.get('upper'):
                            card_orig = '0..*'
                        if not end_dest.get('lower') and not end_dest.get('upper'):
                            card_dest = '0..*'

                    # Validar contra regex del modelo
                    if not re.match(r'^([0-9]+|\*|[0-9]+\.\.([0-9]+|\*))$', card_orig):
                        card_orig = '0..*' if ent_intermedia else '1'
                    if not re.match(r'^([0-9]+|\*|[0-9]+\.\.([0-9]+|\*))$', card_dest):
                        card_dest = '0..*' if ent_intermedia else '1'

                    puerto_orig, puerto_dest = self._calcular_puertos_relacion(origen_ent, destino_ent, uso_puertos)

                    rel_obj = Relacion.objects.create(
                        proyecto=self.proyecto,
                        entidad_origen=origen_ent,
                        entidad_destino=destino_ent,
                        clase_asociacion=ent_intermedia,
                        nombre_relacion=assoc_data['name'] or '',
                        tipo=tipo_rel,
                        cardinalidad_origen=card_orig,
                        cardinalidad_destino=card_dest,
                        puerto_origen=puerto_orig,
                        puerto_destino=puerto_dest,
                    )
                    relaciones_creadas_objs.append(rel_obj)
                    relaciones_creadas += 1

            # B. Relaciones de Herencia a partir de generalizations
            for sub_eaid, sup_eaid in generalizations:
                if sub_eaid in eaid_to_entidad and sup_eaid in eaid_to_entidad:
                    sub_ent = eaid_to_entidad[sub_eaid]
                    sup_ent = eaid_to_entidad[sup_eaid]
                    puerto_sub, puerto_sup = self._calcular_puertos_relacion(sub_ent, sup_ent, uso_puertos)

                    rel_herencia = Relacion.objects.create(
                        proyecto=self.proyecto,
                        entidad_origen=sub_ent,
                        entidad_destino=sup_ent,
                        clase_asociacion=None,
                        nombre_relacion='',
                        tipo=Relacion.Tipo.HERENCIA,
                        cardinalidad_origen='1',
                        cardinalidad_destino='1',
                        puerto_origen=puerto_sub,
                        puerto_destino=puerto_sup,
                    )
                    relaciones_creadas_objs.append(rel_herencia)
                    relaciones_creadas += 1

            # ---------------------------------------------------------------------
            # SNAPSHOT VISUAL: Actualizar datos_diagrama en Proyecto
            # ---------------------------------------------------------------------
            posiciones = {
                str(e.id): {'x': e.coord_x, 'y': e.coord_y}
                for e in eaid_to_entidad.values()
            }
            entidades_snapshot = [
                {
                    'id': e.id,
                    'nombre': e.nombre,
                    'estado': e.estado,
                    'coord_x': e.coord_x,
                    'coord_y': e.coord_y,
                    'ancho': e.ancho,
                    'es_intermedia': e.es_intermedia,
                    'atributos': [
                        {
                            'id': a.id,
                            'nombre': a.nombre,
                            'tipo': a.tipo,
                            'es_clave': a.es_clave,
                            'es_nulo': a.es_nulo,
                            'orden': a.orden,
                        }
                        for a in e.atributos.all().order_by('orden', 'id')
                    ]
                }
                for e in eaid_to_entidad.values()
            ]
            relaciones_snapshot = [
                {
                    'id': r.id,
                    'nombre_relacion': r.nombre_relacion,
                    'tipo': r.tipo,
                    'entidad_origen_id': r.entidad_origen_id,
                    'entidad_destino_id': r.entidad_destino_id,
                    'clase_asociacion_id': r.clase_asociacion_id,
                    'cardinalidad_origen': r.cardinalidad_origen,
                    'cardinalidad_destino': r.cardinalidad_destino,
                    'puerto_origen': r.puerto_origen,
                    'puerto_destino': r.puerto_destino,
                    'vertices': [],
                    'origen_bloqueado': False,
                    'destino_bloqueado': (r.tipo == Relacion.Tipo.COMPOSICION),
                }
                for r in relaciones_creadas_objs
            ]

            self.proyecto.datos_diagrama = {
                'posiciones': posiciones,
                'entidades': entidades_snapshot,
                'relaciones': relaciones_snapshot,
            }
            self.proyecto.save(update_fields=['datos_diagrama', 'fecha_actualizacion'])

        return {
            'entidades_creadas': entidades_creadas,
            'atributos_creados': atributos_creados,
            'relaciones_creadas': relaciones_creadas,
        }
