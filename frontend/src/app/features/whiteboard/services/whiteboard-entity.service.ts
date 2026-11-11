import { Injectable } from '@angular/core';
import * as joint from '@joint/core';

import { EntidadDiagrama } from '../interfaces/diagrama.interface';
import { TemaColores, PosicionEditor } from '../interfaces/whiteboard-ui.interface';
import { etiquetaAtributo, etiquetaOperacion } from '../utils/uml-contract.utils';

const ALTO_HEADER         = 36;
const ALTO_ATRIBUTO       = 24;
const ALTO_BOTON_AGREGAR  = 26;
const ANCHO_MINIMO_TABLA  = 220;

@Injectable()
export class WhiteboardEntityService {
  private graph: joint.dia.Graph | null = null;
  private paper: joint.dia.Paper | null = null;
  private lienzoContainer: HTMLElement | null = null;
  private canvasMedidorCtx: CanvasRenderingContext2D | null = null;

  private celdas            = new Map<number, joint.dia.Element>();
  private celdaIdAEntidadId = new Map<string, number>();
  private entidadesMap      = new Map<number, EntidadDiagrama>();

  public conectar(graph: joint.dia.Graph, paper: joint.dia.Paper, container: HTMLElement): void {
    this.graph = graph;
    this.paper = paper;
    this.lienzoContainer = container;
  }

  public desconectar(): void {
    this.limpiar();
    this.graph = null;
    this.paper = null;
    this.lienzoContainer = null;
  }

  public limpiar(): void {
    this.celdas.clear();
    this.celdaIdAEntidadId.clear();
    this.entidadesMap.clear();
  }

  // ── Medición y Geometría ─────────────────────────────────────────────────

  public medirAnchoTexto(texto: string, font: string): number {
    if (!this.canvasMedidorCtx && typeof document !== 'undefined') {
      const canvas = document.createElement('canvas');
      this.canvasMedidorCtx = canvas.getContext('2d');
    }
    if (this.canvasMedidorCtx) {
      this.canvasMedidorCtx.font = font;
      return Math.ceil(this.canvasMedidorCtx.measureText(texto).width);
    }
    return texto.length * 8;
  }

  public calcularAnchoDinamico(entidad: EntidadDiagrama): number {
    const PADDING_HORIZONTAL = 36;

    const tieneNombre = entidad.nombre && entidad.nombre.trim().length > 0;
    const estereotipo = entidad.tipo_clasificador === 'interfaz' ? '«interface» ' : '';
    const textoNombre = estereotipo + (tieneNombre ? entidad.nombre.trim() : '— nombre entidad —');
    const anchoNombre = this.medirAnchoTexto(textoNombre, '700 13px "JetBrains Mono", monospace') + PADDING_HORIZONTAL + 20;

    const anchoBoton = this.medirAnchoTexto('+ Agregar atributo', '400 11px "JetBrains Mono", monospace') + PADDING_HORIZONTAL;

    let maxAnchoAtributos = 0;
    if (entidad.atributos && entidad.atributos.length > 0) {
      for (const attr of entidad.atributos) {
        const nombreLimpio = attr.nombre.replace(/^[-+~#]\s*/, '').replace(/\[\s*\]/g, '').trim();
        const pk = attr.es_clave ? '[PK] ' : '     ';
        const linea = `${pk}- ${nombreLimpio} : ${attr.tipo}`;
        const anchoLinea = this.medirAnchoTexto(linea, '400 11px "JetBrains Mono", monospace') + PADDING_HORIZONTAL;
        if (anchoLinea > maxAnchoAtributos) {
          maxAnchoAtributos = anchoLinea;
        }
      }
    }

    return Math.max(ANCHO_MINIMO_TABLA, anchoNombre, anchoBoton, maxAnchoAtributos);
  }

  // ── Creación y Renderizado de Celdas ─────────────────────────────────────

  public crearCelda(entidad: EntidadDiagrama, tema: TemaColores): joint.dia.Element | null {
    if (!this.graph) return null;

    const celdaPrevia = this.celdas.get(entidad.id);
    if (celdaPrevia) {
      celdaPrevia.remove();
      this.celdaIdAEntidadId.delete(celdaPrevia.id as string);
    }

    const ancho = entidad.ancho > 0 ? entidad.ancho : this.calcularAnchoDinamico(entidad);
    entidad.ancho = ancho;
    const numLineas = (entidad.atributos?.length ?? 0) + (entidad.operaciones?.length ?? 0) + 1;
    const alto = ALTO_HEADER + (numLineas * ALTO_ATRIBUTO) + ALTO_BOTON_AGREGAR + 14;

const PUERTOS_ITEMS = [
  // 3 puertos en el borde superior
  { id: 'top-0', group: 'top' },
  { id: 'top-1', group: 'top' },
  { id: 'top-2', group: 'top' },
  // 3 puertos en el borde inferior
  { id: 'bottom-0', group: 'bottom' },
  { id: 'bottom-1', group: 'bottom' },
  { id: 'bottom-2', group: 'bottom' },
  // 4 puertos en el borde izquierdo
  { id: 'left-0', group: 'left' },
  { id: 'left-1', group: 'left' },
  { id: 'left-2', group: 'left' },
  { id: 'left-3', group: 'left' },
  // 4 puertos en el borde derecho
  { id: 'right-0', group: 'right' },
  { id: 'right-1', group: 'right' },
  { id: 'right-2', group: 'right' },
  { id: 'right-3', group: 'right' }
];

function generarGruposPuertos(tema: TemaColores) {
  const esOscuro = tema.lienzo === '#111111';
  const portFill = esOscuro ? '#1E293B' : '#FFFFFF';
  const portStroke = esOscuro ? '#38BDF8' : '#0284C7';

  const attrsBase = {
    portBody: {
      r: 4.5,
      magnet: true,
      fill: portFill,
      stroke: portStroke,
      strokeWidth: 1.8,
      cursor: 'crosshair'
    }
  };

  const markup = [{ tagName: 'circle', selector: 'portBody' }];

  return {
    top:    { position: { name: 'top' },    attrs: attrsBase, markup },
    bottom: { position: { name: 'bottom' }, attrs: attrsBase, markup },
    left:   { position: { name: 'left' },   attrs: attrsBase, markup },
    right:  { position: { name: 'right' },  attrs: attrsBase, markup }
  };
}

    const celda = new joint.shapes.standard.HeaderedRectangle({
      position: { x: entidad.coord_x, y: entidad.coord_y },
      size:     { width: ancho, height: alto },
      markup: [
        { tagName: 'rect', selector: 'body' },
        { tagName: 'rect', selector: 'header' },
        { tagName: 'text', selector: 'headerText' },
        { tagName: 'text', selector: 'lockBadge' },
        { tagName: 'text', selector: 'bodyText' }
      ],
      ports: {
        groups: generarGruposPuertos(tema),
        items: PUERTOS_ITEMS
      },
      attrs: {
        root: {
          cursor: 'move',
          class: 'joint-element figura-entidad-lienzo',
          'data-entidad-id': entidad.id
        },
        body: {
          fill:        tema.entidadFondo,
          stroke:      tema.entidadBorde,
          strokeWidth: 1.5,
          rx:          6,
          ry:          6,
          magnet:      'passive'
        },
        header: {
          fill:        tema.headerFondo,
          stroke:      tema.headerBorde,
          strokeWidth: 1.5,
          height:      ALTO_HEADER,
          rx:          6,
          ry:          6,
          magnet:      'passive'
        },
        headerText: {
          text:               '',
          fill:               tema.headerTexto,
          fontSize:           13,
          fontFamily:         '"JetBrains Mono", monospace',
          fontWeight:         '700',
          textAnchor:         'middle',
          x:                  'calc(w/2)',
          y:                  ALTO_HEADER / 2,
          pointerEvents:      'none'
        },
        lockBadge: {
          text:               entidad.estado === 'bloqueado' ? '🔒' : '',
          display:            entidad.estado === 'bloqueado' ? 'block' : 'none',
          fill:               tema.bloqueadoBorde,
          fontSize:           12,
          fontFamily:         '"JetBrains Mono", sans-serif',
          textAnchor:         'end',
          x:                  'calc(w - 10)',
          y:                  ALTO_HEADER / 2,
          textVerticalAnchor: 'middle',
          pointerEvents:      'none'
        },
        bodyText: {
          text:               '',
          fill:               tema.bodyTexto,
          fontSize:           11,
          fontFamily:         '"JetBrains Mono", monospace',
          textAnchor:         'start',
          x:                  14,
          y:                  ALTO_HEADER + 12,
          textVerticalAnchor: 'top',
          lineHeight:         ALTO_ATRIBUTO,
          pointerEvents:      'none'
        }
      }
    });

    this.graph.addCell(celda);
    this.celdas.set(entidad.id, celda);
    this.celdaIdAEntidadId.set(celda.id as string, entidad.id);

    this.actualizarCeldaVisual(entidad, tema, true);

    return celda;
  }

  public actualizarCeldaVisual(entidad: EntidadDiagrama, tema: TemaColores, preservarAncho = false): void {
    const celda = this.celdas.get(entidad.id);
    if (!celda) return;

    const ancho = preservarAncho && entidad.ancho > 0 ? entidad.ancho : Math.max(entidad.ancho || 0, this.calcularAnchoDinamico(entidad));
    entidad.ancho = ancho;
    const numLineas = (entidad.atributos?.length ?? 0) + (entidad.operaciones?.length ?? 0) + 1;
    const alto = ALTO_HEADER + (numLineas * ALTO_ATRIBUTO) + ALTO_BOTON_AGREGAR + 14;

    celda.resize(ancho, alto);

    const tieneNombre = entidad.nombre && entidad.nombre.trim().length > 0;
    const estereotipoVisual = entidad.tipo_clasificador === 'interfaz' ? '«interface» ' : '';
    const textoNombre = estereotipoVisual + (tieneNombre ? entidad.nombre.trim() : '— nombre entidad —');
    const colorNombre = tieneNombre ? tema.headerTexto : 'rgba(128,128,128,0.5)';

    celda.attr('headerText/text', textoNombre);
    celda.attr('headerText/fill', colorNombre);
    celda.attr('headerText/fontStyle', entidad.abstracto ? 'italic' : 'normal');

    const lineas: string[] = [];

    if (entidad.atributos && entidad.atributos.length > 0) {
      const ordenados = [...entidad.atributos].sort((a, b) => a.orden - b.orden);
      ordenados.forEach(attr => {
        lineas.push(etiquetaAtributo(attr, this.entidadesMap));
      });
    }

    if (entidad.operaciones?.length) {
      lineas.push('──────── operaciones ────────');
      [...entidad.operaciones].sort((a, b) => a.orden - b.orden)
        .forEach(op => lineas.push(etiquetaOperacion(op, this.entidadesMap)));
    }

    lineas.push('+ Agregar atributo');

    const esBloqueado = entidad.estado === 'bloqueado';
    const colorBorde = esBloqueado ? tema.bloqueadoBorde : tema.entidadBorde;
    const colorHeaderBorde = esBloqueado ? tema.bloqueadoBorde : tema.headerBorde;

    celda.attr('bodyText/text', lineas.join('\n'));
    celda.attr('bodyText/textAnchor', 'start');
    celda.attr('bodyText/x', 14);
    celda.attr('bodyText/y', ALTO_HEADER + 12);
    celda.attr('bodyText/textVerticalAnchor', 'top');
    celda.attr('bodyText/lineHeight', ALTO_ATRIBUTO);
    celda.attr('bodyText/fill', tema.bodyTexto);
    celda.attr('body/fill', tema.entidadFondo);
    celda.attr('body/stroke', colorBorde);
    celda.attr('header/fill', tema.headerFondo);
    celda.attr('header/stroke', colorHeaderBorde);
    celda.attr('lockBadge/text', esBloqueado ? '🔒' : '');
    celda.attr('lockBadge/display', esBloqueado ? 'block' : 'none');

    const esOscuro = tema.lienzo === '#111111';
    const portFill = esOscuro ? '#1E293B' : '#FFFFFF';
    const portStroke = esOscuro ? '#38BDF8' : '#0284C7';

    ['top', 'bottom', 'left', 'right'].forEach(grp => {
      celda.prop(`ports/groups/${grp}/attrs/portBody/fill`, portFill);
      celda.prop(`ports/groups/${grp}/attrs/portBody/stroke`, portStroke);
    });
  }

  public renderizarEntidades(entidades: EntidadDiagrama[], tema: TemaColores): void {
    this.limpiar();
    entidades.forEach(e => {
      this.entidadesMap.set(e.id, { ...e, atributos: (e.atributos || []).map(a => ({...a})), operaciones: (e.operaciones || []).map(o => ({...o, parametros: (o.parametros || []).map(p => ({...p}))})) });
      this.crearCelda(e, tema);
    });
  }

  public crearEntidadLocal(coordX: number, coordY: number, nuevoId: number, tema: TemaColores): EntidadDiagrama {
    const ancho = ANCHO_MINIMO_TABLA;
    const entidadLocal: EntidadDiagrama = {
      id: nuevoId,
      nombre: '',
      estado: 'activo',
      coord_x: coordX,
      coord_y: coordY,
      ancho,
      es_intermedia: false,
      tipo_clasificador: 'clase',
      abstracto: false,
      atributos: [],
      operaciones: []
    };
    this.entidadesMap.set(entidadLocal.id, entidadLocal);
    this.crearCelda(entidadLocal, tema);
    return entidadLocal;
  }

  public actualizarEntidadLocal(entidad: EntidadDiagrama, tema: TemaColores): void {
    this.entidadesMap.set(entidad.id, entidad);
    this.actualizarCeldaVisual(entidad, tema);
  }

  public aplicarTema(tema: TemaColores): void {
    this.entidadesMap.forEach(entidad => {
      this.actualizarCeldaVisual(entidad, tema);
    });
  }

  // ── Sincronización Remota ────────────────────────────────────────────────

  public moverCeldaRemota(id: number, x: number, y: number): void {
    // Presencia visual: no incorporar movimientos remotos a?n no confirmados
    // en el siguiente autosave del usuario local.
    const celda = this.celdas.get(id);
    if (celda) {
      celda.position(x, y);
    }
  }

  public crearCeldaRemota(entidad: EntidadDiagrama, tema: TemaColores): void {
    if (this.entidadesMap.has(entidad.id)) {
      this.actualizarCeldaRemota(entidad, tema);
      return;
    }
    const copia: EntidadDiagrama = {
      ...entidad,
      atributos: (entidad.atributos || []).map(a => ({...a})),
      operaciones: (entidad.operaciones || []).map(o => ({...o, parametros: (o.parametros || []).map(p => ({...p}))}))
    };
    this.entidadesMap.set(copia.id, copia);
    this.crearCelda(copia, tema);
  }

  public actualizarCeldaRemota(entidad: EntidadDiagrama, tema: TemaColores): void {
    const numId = Number(entidad.id);
    const existente = this.entidadesMap.get(numId);
    if (!existente) {
      this.crearCeldaRemota(entidad, tema);
      return;
    }
    existente.nombre = entidad.nombre;
    existente.tipo_clasificador = entidad.tipo_clasificador ?? existente.tipo_clasificador ?? 'clase';
    existente.abstracto = entidad.abstracto ?? existente.abstracto ?? false;
    existente.atributos = entidad.atributos ? entidad.atributos.map(a => ({...a})) : existente.atributos;
    existente.operaciones = entidad.operaciones ? entidad.operaciones.map(o => ({...o, parametros: (o.parametros || []).map(p => ({...p}))})) : existente.operaciones;
    existente.ancho = entidad.ancho;
    existente.coord_x = Number(entidad.coord_x);
    existente.coord_y = Number(entidad.coord_y);

    if (entidad.estado) {
      existente.estado = entidad.estado;
    }

    const celda = this.celdas.get(numId);
    if (celda && !isNaN(existente.coord_x) && !isNaN(existente.coord_y)) {
      celda.position(existente.coord_x, existente.coord_y);
    }

    this.actualizarCeldaVisual(existente, tema);
  }

  public eliminarCeldaRemota(entidadId: number): void {
    const numId = Number(entidadId);
    const celda = this.celdas.get(numId);
    if (celda) {
      celda.remove();
      this.celdas.delete(numId);
      this.celdaIdAEntidadId.delete(celda.id as string);
    }
    this.entidadesMap.delete(numId);
  }

  public cambiarBorde(id: number, color: string): void {
    const celda = this.celdas.get(id);
    if (celda) {
      celda.attr('body/stroke',   color);
      celda.attr('header/stroke', color);
    }
  }

  public setEstadoBloqueoEntidad(id: number, bloqueado: boolean, tema: TemaColores): void {
    const numId = Number(id);
    const entidad = this.entidadesMap.get(numId);
    if (entidad) {
      entidad.estado = bloqueado ? 'bloqueado' : 'activo';
    }
    const celda = this.celdas.get(numId);
    if (celda) {
      const colorBorde = bloqueado ? tema.bloqueadoBorde : tema.entidadBorde;
      const colorHeaderBorde = bloqueado ? tema.bloqueadoBorde : tema.headerBorde;
      celda.attr('body/stroke', colorBorde);
      celda.attr('header/stroke', colorHeaderBorde);
      celda.attr('lockBadge/text', bloqueado ? '🔒' : '');
      celda.attr('lockBadge/display', bloqueado ? 'block' : 'none');
    }
  }

  // ── Posicionamiento de Editores Inline ───────────────────────────────────

  public obtenerPosicionEditorNombre(entidadId: number): PosicionEditor | null {
    const entidad = this.entidadesMap.get(entidadId);
    const celda = this.celdas.get(entidadId);
    if (!entidad || !celda || !this.paper || !this.lienzoContainer) return null;

    const pos = celda.position();
    const ancho = entidad.ancho || ANCHO_MINIMO_TABLA;
    const clientRect = this.paper.localToClientRect(pos.x, pos.y, ancho, ALTO_HEADER);
    const wrapperRect = this.lienzoContainer.parentElement!.getBoundingClientRect();

    return {
      x: Math.round(clientRect.x - wrapperRect.left),
      y: Math.round(clientRect.y - wrapperRect.top),
      w: Math.round(clientRect.width),
      h: Math.round(clientRect.height)
    };
  }

  public obtenerPosicionEditorNuevoAtributo(entidadId: number): PosicionEditor | null {
    const entidad = this.entidadesMap.get(entidadId);
    const celda = this.celdas.get(entidadId);
    if (!entidad || !celda || !this.paper || !this.lienzoContainer) return null;

    const pos = celda.position();
    const ancho = entidad.ancho || ANCHO_MINIMO_TABLA;
    const numAtributos = entidad.atributos?.length ?? 0;
    const localY = pos.y + ALTO_HEADER + 8 + (numAtributos * ALTO_ATRIBUTO);

    const clientRect = this.paper.localToClientRect(pos.x + 8, localY, ancho - 16, ALTO_ATRIBUTO);
    const wrapperRect = this.lienzoContainer.parentElement!.getBoundingClientRect();

    return {
      x: Math.round(clientRect.x - wrapperRect.left),
      y: Math.round(clientRect.y - wrapperRect.top),
      w: Math.round(clientRect.width),
      h: Math.round(clientRect.height)
    };
  }

  public obtenerPosicionEditorAtributo(entidadId: number, index: number): PosicionEditor | null {
    const entidad = this.entidadesMap.get(entidadId);
    const celda = this.celdas.get(entidadId);
    if (!entidad || !celda || !this.paper || !this.lienzoContainer) return null;

    const pos = celda.position();
    const ancho = entidad.ancho || ANCHO_MINIMO_TABLA;
    const localY = pos.y + ALTO_HEADER + 8 + (index * ALTO_ATRIBUTO);

    const clientRect = this.paper.localToClientRect(pos.x + 8, localY, ancho - 16, ALTO_ATRIBUTO);
    const wrapperRect = this.lienzoContainer.parentElement!.getBoundingClientRect();

    return {
      x: Math.round(clientRect.x - wrapperRect.left),
      y: Math.round(clientRect.y - wrapperRect.top),
      w: Math.round(clientRect.width),
      h: Math.round(clientRect.height)
    };
  }

  // ── Getters de Estado ────────────────────────────────────────────────────

  public getEntidad(id: number): EntidadDiagrama | undefined {
    return this.entidadesMap.get(id);
  }

  public getCelda(id: number): joint.dia.Element | undefined {
    return this.celdas.get(id);
  }

  public getEntidadIdPorCeldaId(celdaId: string): number | undefined {
    return this.celdaIdAEntidadId.get(celdaId);
  }

  public getCantidadEntidades(): number {
    return this.entidadesMap.size;
  }

  public obtenerPosiciones(): Record<number, { x: number; y: number }> {
    const posiciones: Record<number, { x: number; y: number }> = {};
    this.entidadesMap.forEach((entidad, id) => {
      posiciones[id] = { x: entidad.coord_x, y: entidad.coord_y };
    });
    return posiciones;
  }

  public getEntidades(): EntidadDiagrama[] {
    const lista: EntidadDiagrama[] = [];
    this.entidadesMap.forEach((ent, id) => {
      lista.push({
        ...ent,
        coord_x: ent.coord_x,
        coord_y: ent.coord_y,
        ancho: ent.ancho,
        es_intermedia: ent.es_intermedia ?? false,
        atributos: ent.atributos ? ent.atributos.map(a => ({ ...a })) : [],
        operaciones: (ent.operaciones || []).map(o => ({ ...o, parametros: (o.parametros || []).map(p => ({...p})) }))
      });
    });
    return lista;
  }

  public remapIds(idMap?: Record<string | number, number>, attrIdMap?: Record<string | number, number>, operationIdMap?: Record<string | number, number>, parameterIdMap?: Record<string | number, number>): void {
    if (!idMap && !attrIdMap && !operationIdMap && !parameterIdMap) return;
    this.entidadesMap.forEach(entidad => {
      entidad.atributos = (entidad.atributos || []).map(a => ({ ...a, id: attrIdMap?.[a.id] ?? a.id,
        tipo_referencia_id: a.tipo_referencia_id == null ? a.tipo_referencia_id : (idMap?.[a.tipo_referencia_id] ?? a.tipo_referencia_id) }));
      entidad.operaciones = (entidad.operaciones || []).map(o => ({ ...o, id: operationIdMap?.[o.id] ?? o.id,
        retorno_referencia_id: o.retorno_referencia_id == null ? o.retorno_referencia_id : (idMap?.[o.retorno_referencia_id] ?? o.retorno_referencia_id),
        parametros: (o.parametros || []).map(p => ({ ...p, id: parameterIdMap?.[p.id] ?? p.id,
          tipo_referencia_id: p.tipo_referencia_id == null ? p.tipo_referencia_id : (idMap?.[p.tipo_referencia_id] ?? p.tipo_referencia_id) })) }));
    });
    if (!idMap) return;
    for (const [oldIdStr, newId] of Object.entries(idMap)) {
      const oldId = Number(oldIdStr);
      if (oldId === newId) continue;

      const entidad = this.entidadesMap.get(oldId);
      if (entidad) {
        this.entidadesMap.delete(oldId);
        entidad.id = newId;
        this.entidadesMap.set(newId, entidad);
      }

      const celda = this.celdas.get(oldId);
      if (celda) {
        this.celdas.delete(oldId);
        this.celdas.set(newId, celda);
        this.celdaIdAEntidadId.set(celda.id as string, newId);
      }
    }
  }
}
