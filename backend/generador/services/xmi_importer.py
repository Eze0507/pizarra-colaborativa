import re
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction
from modelado.models import Proyecto, Entidad, Atributo, Relacion, Operacion, ParametroOperacion

XMI_NS = 'http://schema.omg.org/spec/XMI/2.1'
UML_NS = 'http://schema.omg.org/spec/UML/2.1'
SUPPORTED_JPA_KEY_TYPES = {
    Atributo.Tipo.STRING,
    Atributo.Tipo.INTEGER,
    Atributo.Tipo.LONG,
}

LEGACY_FK_ATTRIBUTE_RE = re.compile(
    r'^\s*(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*'
    r'\(\s*FK\s*;\s*(?P<target>[^)]+?)\s*\)\s*[}\]]*\s*$',
    re.IGNORECASE,
)


def parse_legacy_fk_attribute_name(value: str) -> Tuple[str, Optional[str]]:
    """Separa ``campo(FK; tabla)`` sin inventar ni alterar la relación UML."""
    raw = (value or '').strip()
    match = LEGACY_FK_ATTRIBUTE_RE.fullmatch(raw)
    if not match:
        return raw, None
    return match.group('name'), match.group('target').strip()


def resolve_legacy_fk_name_collisions(attributes: List[Dict[str, Any]]) -> None:
    """Hace únicos solo los nombres FK anotados; no oculta duplicados UML comunes."""
    plain_names = {
        item['nombre'] for item in attributes if item.get('fk_target_name') is None
    }
    used_names: set[str] = set()
    for item in attributes:
        base_name = item['nombre']
        target_name = item.get('fk_target_name')
        candidate = base_name
        if target_name is not None and (candidate in plain_names or candidate in used_names):
            suffix = re.sub(r'[^A-Za-z0-9_$]+', '_', target_name).strip('_') or 'ref'
            candidate = f'{base_name}_{suffix}'
            numbered_candidate = candidate
            sequence = 2
            while numbered_candidate in plain_names or numbered_candidate in used_names:
                numbered_candidate = f'{candidate}_{sequence}'
                sequence += 1
            candidate = numbered_candidate
        item['nombre'] = candidate
        used_names.add(candidate)


def prepare_imported_persistence(
    raw_classes: Dict[str, Dict[str, Any]],
    preserved_keys: Optional[Dict[str, str]] = None,
) -> Dict[str, int]:
    """Prepara JPA solo cuando existe una clave simple inequívoca y compatible."""
    preserved_keys = preserved_keys or {}
    imported_name_counts = Counter(
        str(item.get('nombre') or '').casefold() for item in raw_classes.values()
    )
    metrics = {
        'entidades_persistentes': 0,
        'claves_explicitamente_importadas': 0,
        'claves_preservadas': 0,
        'claves_id_inferidas': 0,
        'entidades_no_elegibles_persistencia': 0,
    }

    for class_data in raw_classes.values():
        if (
            class_data.get('tipo_clasificador') == Entidad.TipoClasificador.INTERFAZ
            or class_data.get('abstracto')
        ):
            metrics['entidades_no_elegibles_persistencia'] += 1
            continue

        attributes = class_data.get('atributos', [])
        explicit_keys = [item for item in attributes if item.get('es_clave')]
        key = None
        source = None

        if explicit_keys:
            if len(explicit_keys) == 1:
                key = explicit_keys[0]
                source = 'explicit'
        else:
            class_name = str(class_data.get('nombre') or '').casefold()
            preserved_name = (
                preserved_keys.get(class_name)
                if imported_name_counts[class_name] == 1
                else None
            )
            if preserved_name:
                preserved_matches = [
                    item for item in attributes
                    if str(item.get('nombre') or '').casefold() == preserved_name
                ]
                if len(preserved_matches) == 1:
                    key = preserved_matches[0]
                    source = 'preserved'

            if key is None:
                id_matches = [
                    item for item in attributes
                    if str(item.get('nombre') or '').casefold() == 'id'
                ]
                if len(id_matches) == 1:
                    key = id_matches[0]
                    source = 'inferred'

        if key is None or key.get('tipo') not in SUPPORTED_JPA_KEY_TYPES:
            metrics['entidades_no_elegibles_persistencia'] += 1
            continue

        key['es_clave'] = True
        key['es_nulo'] = False
        class_data['tipo_clasificador'] = Entidad.TipoClasificador.ENTIDAD_PERSISTENTE
        metrics['entidades_persistentes'] += 1
        if source == 'explicit':
            metrics['claves_explicitamente_importadas'] += 1
        elif source == 'preserved':
            metrics['claves_preservadas'] += 1
        else:
            metrics['claves_id_inferidas'] += 1

    return metrics


def remove_hidden_duplicate_classifiers(
    raw_classes: Dict[str, Dict[str, Any]],
    raw_associations: Dict[str, Dict[str, Any]],
    generalizations: List[Tuple[str, str]],
    realizations: List[Tuple[str, str]],
    diagram_positions: Dict[str, Dict[str, float]],
) -> int:
    """Omite solo copias identicas, ocultas y sin referencias del XMI.

    Enterprise Architect puede conservar elementos eliminados del diagrama dentro
    del modelo XMI. Un nombre repetido sigue siendo un error UML salvo cuando hay
    exactamente una copia visible o referenciada y las demas son copias
    estructuralmente identicas que no participan en ninguna referencia.
    """

    def reference_name(reference: Optional[str]) -> Optional[str]:
        target = raw_classes.get(reference or '')
        if target is None:
            return reference
        return str(target.get('nombre') or '').casefold()

    def signature(class_data: Dict[str, Any]) -> Tuple[Any, ...]:
        attributes = tuple(
            (
                item.get('nombre'), item.get('tipo'),
                reference_name(item.get('tipo_ref_eaid')),
                item.get('visibilidad'), bool(item.get('es_estatico')),
                item.get('valor_predeterminado'), bool(item.get('es_nulo')),
                bool(item.get('es_clave')),
            )
            for item in class_data.get('atributos', [])
        )
        operations = tuple(
            (
                item.get('nombre'), item.get('visibilidad'),
                item.get('tipo_retorno'),
                reference_name(item.get('retorno_ref_eaid')),
                bool(item.get('es_estatico')), bool(item.get('es_abstracto')),
                tuple(
                    (
                        parameter.get('nombre'), parameter.get('tipo'),
                        reference_name(parameter.get('tipo_ref_eaid')),
                    )
                    for parameter in item.get('parametros', [])
                ),
            )
            for item in class_data.get('operaciones', [])
        )
        return (
            bool(class_data.get('es_intermedia')),
            class_data.get('tipo_clasificador'),
            bool(class_data.get('abstracto')),
            attributes,
            operations,
        )

    referenced: set[str] = set()
    for association_id, association in raw_associations.items():
        if association.get('is_assoc_class'):
            referenced.add(association_id)
        referenced.update(
            end['class_id']
            for end in association.get('ends', [])
            if end.get('class_id')
        )
    for source, target in [*generalizations, *realizations]:
        referenced.update((source, target))
    for class_data in raw_classes.values():
        for attribute in class_data.get('atributos', []):
            if attribute.get('tipo_ref_eaid') in raw_classes:
                referenced.add(attribute['tipo_ref_eaid'])
        for operation in class_data.get('operaciones', []):
            if operation.get('retorno_ref_eaid') in raw_classes:
                referenced.add(operation['retorno_ref_eaid'])
            for parameter in operation.get('parametros', []):
                if parameter.get('tipo_ref_eaid') in raw_classes:
                    referenced.add(parameter['tipo_ref_eaid'])

    groups: Dict[str, List[str]] = {}
    for class_id, class_data in raw_classes.items():
        groups.setdefault(str(class_data.get('nombre') or '').casefold(), []).append(class_id)

    omitted = 0
    for class_ids in groups.values():
        if len(class_ids) < 2:
            continue
        active = [
            class_id for class_id in class_ids
            if class_id in diagram_positions or class_id in referenced
        ]
        if len(active) != 1:
            continue
        if len({signature(raw_classes[class_id]) for class_id in class_ids}) != 1:
            continue
        for class_id in class_ids:
            if class_id == active[0]:
                continue
            del raw_classes[class_id]
            omitted += 1
    return omitted


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

        # Si no se especifica ni lowerValue ni upperValue, la relación no tiene cardinalidad en este extremo
        if not l_val and not u_val:
            return ''

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

    def _extraer_atributos_pk_ea(self, root: ET.Element) -> Tuple[set, set]:
        """
        Escanea las extensiones de Enterprise Architect (<xmi:Extension>) buscando atributos
        que tengan activada la propiedad 'is ID' (isID=1 / isID=true) o estereotipo PK.
        Retorna:
            - pk_ids: Conjunto de IDs de atributos (xmi:idref / xmi:id).
            - pk_class_attr_names: Conjunto de tuplas (class_idref, nombre_attr_lower) para respaldo.
        """
        pk_ids = set()
        pk_class_attr_names = set()

        for elem in root.iter():
            tag = self._limpiar_tag(elem)
            if tag == 'element':
                class_idref = self._obtener_attr(elem, 'idref') or self._obtener_attr(elem, 'id')
                for child in elem:
                    if self._limpiar_tag(child) == 'attributes':
                        for attr_elem in child:
                            if self._limpiar_tag(attr_elem) == 'attribute':
                                attr_id = self._obtener_attr(attr_elem, 'idref') or self._obtener_attr(attr_elem, 'id')
                                attr_name = attr_elem.attrib.get('name')

                                is_pk = False

                                # 1. Revisar xrefs de EA: @PROP=@NAME=isID@ENDNAME;@TYPE=Boolean@ENDTYPE;@VALU=1@ENDVALU;
                                xrefs_val = ''
                                for x in attr_elem:
                                    if self._limpiar_tag(x) == 'xrefs':
                                        xrefs_val = x.attrib.get('value', '') or (x.text or '')
                                xrefs_val += attr_elem.attrib.get('xrefs', '')

                                if '@NAME=isID@ENDNAME;' in xrefs_val and ('@VALU=1@ENDVALU;' in xrefs_val or '@VALU=true@ENDVALU;' in xrefs_val):
                                    is_pk = True

                                # 2. Revisar estereotipo PK (<stereotype name="PK"/> o atributo stereotype="PK")
                                for s in attr_elem:
                                    if self._limpiar_tag(s) == 'stereotype':
                                        st_val = s.attrib.get('name') or s.attrib.get('value') or s.text or ''
                                        if 'PK' in st_val.upper() or 'PRIMARYKEY' in st_val.upper():
                                            is_pk = True
                                st_attr = attr_elem.attrib.get('stereotype', '')
                                if 'PK' in st_attr.upper() or 'PRIMARYKEY' in st_attr.upper():
                                    is_pk = True

                                # 3. Revisar tags de EA (<tags><tag name="isID" value="1"/></tags>)
                                for tg in attr_elem:
                                    if self._limpiar_tag(tg) == 'tags':
                                        for t in tg:
                                            t_name = (t.attrib.get('name') or '').lower()
                                            t_val = (t.attrib.get('value') or t.text or '').lower()
                                            if t_name in ('isid', 'pk', 'primarykey') and t_val in ('1', 'true', 'yes'):
                                                is_pk = True

                                # 4. Revisar properties de EA (<properties isID="1" ... />)
                                for pr in attr_elem:
                                    if self._limpiar_tag(pr) == 'properties':
                                        if pr.attrib.get('isID') in ('1', 'true', True) or pr.attrib.get('isId') in ('1', 'true', True):
                                            is_pk = True

                                if is_pk:
                                    if attr_id:
                                        pk_ids.add(attr_id)
                                    if class_idref and attr_name:
                                        pk_class_attr_names.add((class_idref, attr_name.strip().lower()))

        return pk_ids, pk_class_attr_names

    def importar_xml(self, contenido_xml: str, reemplazar_existente: bool = True) -> Dict[str, Any]:
        """
        Parsea el contenido XML e inserta las entidades, atributos y relaciones en la base de datos.
        """
        # Limpieza básica y parseo del XML
        if isinstance(contenido_xml, bytes):
            contenido_xml = contenido_xml.decode('utf-8', errors='replace')

        root = ET.fromstring(contenido_xml)

        # 0. Extraer atributos definidos explícitamente como Primary Key en Enterprise Architect (<xmi:Extension>)
        ea_pk_ids, ea_pk_class_attr_names = self._extraer_atributos_pk_ea(root)

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
        realizations: List[Tuple[str, str]] = []
        atributos_fk_normalizados = 0

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
            if elem_type in ('uml:Class', 'Class', 'uml:Interface', 'Interface', 'uml:AssociationClass', 'AssociationClass') and elem_id:
                is_assoc_class = 'AssociationClass' in elem_type
                attrs_list: List[Dict[str, Any]] = []
                operations_list: List[Dict[str, Any]] = []

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

                    elif child_tag == 'interfaceRealization' or self._obtener_attr(child, 'type') in ('uml:InterfaceRealization', 'InterfaceRealization'):
                        target = child.attrib.get('contract') or child.attrib.get('supplier')
                        if target:
                            realizations.append((elem_id, target))

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
                                'role': child.attrib.get('name', ''),
                                'navigable': child.attrib.get('isNavigable') in ('true', '1'),
                            }
                            association_ends_by_assoc.setdefault(attr_assoc, []).append(end_info)

                        # Si tiene nombre real de columna, es un atributo de la entidad
                        if attr_name:
                            nombre_normalizado, fk_target_name = parse_legacy_fk_attribute_name(attr_name)
                            if fk_target_name is not None:
                                atributos_fk_normalizados += 1

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
                            # Se marca es_clave=True ÚNICAMENTE si está explícitamente definido como tal:
                            # 1. En UML estándar: atributo isID="true" / isID="1" o estereotipo PK en <ownedAttribute>
                            # 2. En Enterprise Architect: registrado con isID=1 en <xmi:Extension> (xrefs, stereotype, tags, properties)
                            attr_id = self._obtener_attr(child, 'id')
                            is_id_uml = (
                                child.attrib.get('isID') in ('true', '1', True) or
                                child.attrib.get('isId') in ('true', '1', True)
                            )

                            child_stereo = child.attrib.get('stereotype', '')
                            for c in child:
                                if self._limpiar_tag(c) == 'stereotype':
                                    child_stereo += ' ' + (c.attrib.get('name') or c.attrib.get('value') or c.text or '')
                            is_pk_stereo = 'PK' in child_stereo.upper() or 'PRIMARYKEY' in child_stereo.upper()

                            es_clave = bool(
                                is_id_uml or
                                is_pk_stereo or
                                (attr_id and attr_id in ea_pk_ids) or
                                (elem_id and attr_name and (elem_id, attr_name.strip().lower()) in ea_pk_class_attr_names)
                            )

                            attrs_list.append({
                                'nombre': nombre_normalizado,
                                'tipo': self._mapear_tipo_dato(tipo_str),
                                'tipo_ref_eaid': tipo_str if tipo_str and not str(tipo_str).startswith('EAJava_') else None,
                                # Se conserva como metadato de importación. Las asociaciones
                                # del XMI siguen siendo la autoridad de las relaciones UML.
                                'fk_target_name': fk_target_name,
                                'visibilidad': child.attrib.get('visibility', 'private'),
                                'es_estatico': child.attrib.get('isStatic') in ('true', '1'),
                                'valor_predeterminado': child.attrib.get('default', ''),
                                'es_nulo': es_nulo,
                                'es_clave': es_clave,
                            })

                    elif child_tag == 'ownedOperation':
                        parametros = []
                        retorno_tipo = 'void'
                        retorno_ref = None
                        for param in child:
                            if self._limpiar_tag(param) != 'ownedParameter':
                                continue
                            tipo_param = None
                            for type_child in param:
                                if self._limpiar_tag(type_child) == 'type':
                                    tipo_param = self._obtener_attr(type_child, 'idref') or type_child.attrib.get('name')
                            if param.attrib.get('direction') == 'return':
                                retorno_tipo = self._mapear_tipo_dato(tipo_param) if tipo_param else 'void'
                                retorno_ref = tipo_param if tipo_param and not str(tipo_param).startswith('EAJava_') else None
                            else:
                                parametros.append({'nombre': param.attrib.get('name') or 'parametro',
                                    'tipo': self._mapear_tipo_dato(tipo_param),
                                    'tipo_ref_eaid': tipo_param if tipo_param and not str(tipo_param).startswith('EAJava_') else None})
                        operations_list.append({
                            'nombre': child.attrib.get('name') or 'operacion',
                            'visibilidad': child.attrib.get('visibility', 'public'),
                            'tipo_retorno': retorno_tipo, 'retorno_ref_eaid': retorno_ref,
                            'es_estatico': child.attrib.get('isStatic') in ('true', '1'),
                            'es_abstracto': child.attrib.get('isAbstract') in ('true', '1'),
                            'parametros': parametros,
                        })

                resolve_legacy_fk_name_collisions(attrs_list)
                is_interface = 'Interface' in elem_type

                raw_classes[elem_id] = {
                    'nombre': elem_name or f"Entidad_{elem_id[-6:]}",
                    'es_intermedia': is_assoc_class,
                    'tipo_clasificador': (
                        Entidad.TipoClasificador.INTERFAZ
                        if is_interface
                        else Entidad.TipoClasificador.CLASE
                    ),
                    'abstracto': elem.attrib.get('isAbstract') in ('true', '1') or is_interface,
                    'atributos': attrs_list,
                    'operaciones': operations_list,
                }

                # Si es AssociationClass, registrarla también como asociación
                # IMPORTANTE: En UML, elem_name es el nombre de la clase/tabla intermedia (ej. userColaborador),
                # NO debe usarse como nombre o etiqueta de la relación a menos que se haya definido explícitamente en el conector.
                if is_assoc_class:
                    raw_associations[elem_id] = {
                        'name': '',
                        'is_assoc_class': True,
                        'ends': [],
                    }

            # --- B. ASOCIACIONES ---
            elif elem_type in ('uml:Association', 'Association') and elem_id:
                raw_associations[elem_id] = {
                    'name': elem_name or '',
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
                            'role': child.attrib.get('name', ''),
                            'navigable': child.attrib.get('isNavigable') in ('true', '1'),
                        })

        # Fusionar extremos externos hallados en ownedAttribute
        for assoc_id, extra_ends in association_ends_by_assoc.items():
            if assoc_id in raw_associations:
                raw_associations[assoc_id]['ends'].extend(extra_ends)

        # 4. Extraer nombres/etiquetas explícitas de conectores desde la extensión de Enterprise Architect (si existe)
        # En Enterprise Architect, el conector para una clase de asociación se vincula mediante:
        # <connector ...><extendedProperties associationclass="EAID_clase_intermedia" .../></connector>
        # Solo si el conector tiene un nombre o etiqueta 'mt' explícita distinta del nombre de la tabla,
        # se debe asignar como nombre_relacion.
        for elem in root.iter():
            if self._limpiar_tag(elem) == 'connector':
                conn_name = elem.attrib.get('name')
                assoc_class_target = None
                for child in elem:
                    ctag = self._limpiar_tag(child)
                    if ctag == 'labels' and not conn_name:
                        conn_name = child.attrib.get('mt')
                    elif ctag == 'extendedProperties':
                        assoc_class_target = child.attrib.get('associationclass')

                final_name = (conn_name or '').strip()

                # Caso AssociationClass: solo asignar si en Architect se nombró explícitamente el conector
                if assoc_class_target and assoc_class_target in raw_associations:
                    class_name = raw_classes.get(assoc_class_target, {}).get('nombre', '')
                    if final_name and final_name.lower() != class_name.lower():
                        raw_associations[assoc_class_target]['name'] = final_name
                    else:
                        raw_associations[assoc_class_target]['name'] = ''

                # Caso Asociación estándar sin nombre en UML pero con nombre en el conector de EA
                conn_idref = self._obtener_attr(elem, 'idref')
                if conn_idref and conn_idref in raw_associations and not raw_associations[conn_idref].get('is_assoc_class'):
                    if not raw_associations[conn_idref]['name'] and final_name:
                        raw_associations[conn_idref]['name'] = final_name

        # 5. Extraer coordenadas visuales desde la sección <diagrams> de Enterprise Architect (si existe)
        # Esto permite preservar exactamente la distribución espacial (arriba/abajo, izquierda/derecha)
        # en lugar de reordenar las entidades en una cuadrícula horizontal arbitraria.
        ea_diagram_positions: Dict[str, Dict[str, float]] = {}
        for elem in root.iter():
            tag = self._limpiar_tag(elem)
            if tag == 'element' and 'geometry' in elem.attrib and 'subject' in elem.attrib:
                geo = elem.attrib['geometry']
                if 'Left=' in geo and 'Top=' in geo:
                    subject = elem.attrib['subject']
                    parts = {}
                    for item in geo.split(';'):
                        if '=' in item:
                            k, v = item.split('=', 1)
                            parts[k.strip()] = v.strip()
                    if 'Left' in parts and 'Top' in parts:
                        try:
                            left_val = float(parts['Left'])
                            top_val = float(parts['Top'])
                            right_val = float(parts.get('Right', left_val + 220.0))
                            bottom_val = float(parts.get('Bottom', top_val + 150.0))

                            x = left_val
                            if top_val < 0 and bottom_val < 0:
                                y = min(abs(top_val), abs(bottom_val))
                            else:
                                y = min(top_val, bottom_val)

                            w = max(abs(right_val - left_val), 200.0)
                            ea_diagram_positions[subject] = {'x': x, 'y': y, 'w': w}
                        except ValueError:
                            pass

        # Normalizar posiciones del diagrama para que inicien en un margen visible seguro (80px, 80px)
        if ea_diagram_positions:
            min_x = min(p['x'] for p in ea_diagram_positions.values())
            min_y = min(p['y'] for p in ea_diagram_positions.values())
            shift_x = 80.0 - min_x
            shift_y = 80.0 - min_y
            for p in ea_diagram_positions.values():
                p['x'] = round(p['x'] + shift_x, 1)
                p['y'] = round(p['y'] + shift_y, 1)

        duplicate_classifiers_omitted = remove_hidden_duplicate_classifiers(
            raw_classes,
            raw_associations,
            generalizations,
            realizations,
            ea_diagram_positions,
        )

        # =========================================================================
        # PROCESAMIENTO EN DOS PASADAS (TWO-PASS PARSING)
        # =========================================================================
        with transaction.atomic():
            preserved_keys: Dict[str, str] = {}
            if reemplazar_existente:
                existing_entities = list(
                    self.proyecto.entidades.prefetch_related('atributos').all()
                )
                existing_name_counts = Counter(
                    entity.nombre.casefold() for entity in existing_entities
                )
                for entity in existing_entities:
                    if (
                        entity.tipo_clasificador
                        != Entidad.TipoClasificador.ENTIDAD_PERSISTENTE
                        or existing_name_counts[entity.nombre.casefold()] != 1
                    ):
                        continue
                    keys = [
                        attribute for attribute in entity.atributos.all()
                        if attribute.es_clave and attribute.tipo in SUPPORTED_JPA_KEY_TYPES
                    ]
                    if len(keys) == 1:
                        preserved_keys[entity.nombre.casefold()] = keys[0].nombre.casefold()

            persistence_metrics = prepare_imported_persistence(
                raw_classes,
                preserved_keys=preserved_keys,
            )

            if reemplazar_existente:
                self.proyecto.relaciones.all().delete()
                self.proyecto.entidades.all().delete()

            eaid_to_entidad: Dict[str, Entidad] = {}
            entidades_creadas = 0
            atributos_creados = 0
            relaciones_creadas = 0
            relaciones_creadas_objs: List[Relacion] = []
            referencias_atributo = []
            referencias_retorno = []
            referencias_parametro = []

            # ---------------------------------------------------------------------
            # PASADA 1: Creación de Entidades y Atributos (Classes y AssociationClasses)
            # ---------------------------------------------------------------------
            cols = 3
            missing_idx = 0
            max_y = max((p['y'] for p in ea_diagram_positions.values()), default=80.0)

            for idx, (eaid, class_data) in enumerate(raw_classes.items()):
                if eaid in ea_diagram_positions:
                    coord_x = ea_diagram_positions[eaid]['x']
                    coord_y = ea_diagram_positions[eaid]['y']
                    ancho = ea_diagram_positions[eaid]['w']
                else:
                    if ea_diagram_positions:
                        col = missing_idx % cols
                        row = missing_idx // cols
                        coord_x = 80.0 + col * 340.0
                        coord_y = max_y + 160.0 + row * 260.0
                        missing_idx += 1
                    else:
                        row = idx // cols
                        col = idx % cols
                        coord_x = 80.0 + col * 340.0
                        coord_y = 80.0 + row * 260.0
                    ancho = 220.0

                entidad = Entidad.objects.create(
                    proyecto=self.proyecto,
                    nombre=class_data['nombre'],
                    estado=Entidad.Estado.ACTIVO,
                    coord_x=coord_x,
                    coord_y=coord_y,
                    ancho=ancho,
                    es_intermedia=class_data['es_intermedia'],
                    tipo_clasificador=class_data.get('tipo_clasificador', Entidad.TipoClasificador.CLASE),
                    abstracto=class_data.get('abstracto', False),
                )
                eaid_to_entidad[eaid] = entidad
                entidades_creadas += 1

                for orden, attr_data in enumerate(class_data['atributos']):
                    atributo = Atributo.objects.create(
                        entidad=entidad,
                        nombre=attr_data['nombre'],
                        tipo=attr_data['tipo'],
                        visibilidad=attr_data.get('visibilidad', 'private'),
                        es_estatico=attr_data.get('es_estatico', False),
                        valor_predeterminado=attr_data.get('valor_predeterminado', ''),
                        es_clave=attr_data['es_clave'],
                        es_nulo=attr_data['es_nulo'],
                        orden=orden,
                    )
                    if attr_data.get('tipo_ref_eaid'):
                        referencias_atributo.append((atributo, attr_data['tipo_ref_eaid']))
                    atributos_creados += 1

                for op_orden, op_data in enumerate(class_data.get('operaciones', [])):
                    operacion = Operacion.objects.create(
                        entidad=entidad, nombre=op_data['nombre'], visibilidad=op_data['visibilidad'],
                        tipo_retorno=op_data['tipo_retorno'], orden=op_orden,
                        es_estatico=op_data['es_estatico'], es_abstracto=op_data['es_abstracto'],
                    )
                    if op_data.get('retorno_ref_eaid'):
                        referencias_retorno.append((operacion, op_data['retorno_ref_eaid']))
                    for p_orden, p_data in enumerate(op_data.get('parametros', [])):
                        parametro = ParametroOperacion.objects.create(
                            operacion=operacion, nombre=p_data['nombre'], tipo=p_data['tipo'], orden=p_orden
                        )
                        if p_data.get('tipo_ref_eaid'):
                            referencias_parametro.append((parametro, p_data['tipo_ref_eaid']))

            for atributo, target_eaid in referencias_atributo:
                if target_eaid in eaid_to_entidad:
                    atributo.tipo_referencia = eaid_to_entidad[target_eaid]
                    atributo.save(update_fields=['tipo_referencia'])
            for operacion, target_eaid in referencias_retorno:
                if target_eaid in eaid_to_entidad:
                    operacion.retorno_referencia = eaid_to_entidad[target_eaid]
                    operacion.save(update_fields=['retorno_referencia'])
            for parametro, target_eaid in referencias_parametro:
                if target_eaid in eaid_to_entidad:
                    parametro.tipo_referencia = eaid_to_entidad[target_eaid]
                    parametro.save(update_fields=['tipo_referencia'])

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

                    # Validar contra regex del modelo solo si se especificó cardinalidad
                    if card_orig and not re.match(r'^([0-9]+|\*|[0-9]+\.\.([0-9]+|\*))$', card_orig):
                        card_orig = ''
                    if card_dest and not re.match(r'^([0-9]+|\*|[0-9]+\.\.([0-9]+|\*))$', card_dest):
                        card_dest = ''

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
                        rol_origen=end_orig.get('role', ''),
                        rol_destino=end_dest.get('role', ''),
                        navegable_origen=end_orig.get('navigable', False),
                        navegable_destino=end_dest.get('navigable', False),
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
                        cardinalidad_origen='',
                        cardinalidad_destino='',
                        puerto_origen=puerto_sub,
                        puerto_destino=puerto_sup,
                    )
                    relaciones_creadas_objs.append(rel_herencia)
                    relaciones_creadas += 1

            # C. Realizaciones de interfaces UML estándar
            for client_eaid, contract_eaid in realizations:
                if client_eaid in eaid_to_entidad and contract_eaid in eaid_to_entidad:
                    client = eaid_to_entidad[client_eaid]
                    contract = eaid_to_entidad[contract_eaid]
                    puerto_client, puerto_contract = self._calcular_puertos_relacion(client, contract, uso_puertos)
                    rel_impl = Relacion.objects.create(
                        proyecto=self.proyecto, entidad_origen=client, entidad_destino=contract,
                        tipo=Relacion.Tipo.IMPLEMENTACION, puerto_origen=puerto_client, puerto_destino=puerto_contract,
                    )
                    relaciones_creadas_objs.append(rel_impl)
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
                    'tipo_clasificador': e.tipo_clasificador,
                    'abstracto': e.abstracto,
                    'atributos': [
                        {
                            'id': a.id,
                            'nombre': a.nombre,
                            'tipo': a.tipo,
                            'tipo_referencia_id': a.tipo_referencia_id,
                            'visibilidad': a.visibilidad,
                            'es_estatico': a.es_estatico,
                            'valor_predeterminado': a.valor_predeterminado,
                            'es_clave': a.es_clave,
                            'es_nulo': a.es_nulo,
                            'orden': a.orden,
                        }
                        for a in e.atributos.all().order_by('orden', 'id')
                    ],
                    'operaciones': [
                        {
                            'id': o.id, 'nombre': o.nombre, 'visibilidad': o.visibilidad,
                            'tipo_retorno': o.tipo_retorno, 'retorno_referencia_id': o.retorno_referencia_id,
                            'orden': o.orden, 'es_estatico': o.es_estatico, 'es_abstracto': o.es_abstracto,
                            'parametros': [
                                {'id': p.id, 'nombre': p.nombre, 'tipo': p.tipo,
                                 'tipo_referencia_id': p.tipo_referencia_id, 'orden': p.orden}
                                for p in o.parametros.all().order_by('orden', 'id')
                            ],
                        }
                        for o in e.operaciones.all().order_by('orden', 'id')
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
                    'rol_origen': r.rol_origen,
                    'rol_destino': r.rol_destino,
                    'navegable_origen': r.navegable_origen,
                    'navegable_destino': r.navegable_destino,
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
            'atributos_fk_normalizados': atributos_fk_normalizados,
            'clasificadores_duplicados_omitidos': duplicate_classifiers_omitted,
            **persistence_metrics,
        }
