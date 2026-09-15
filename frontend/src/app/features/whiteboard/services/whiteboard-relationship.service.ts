import { Injectable, inject } from '@angular/core';
import * as joint from '@joint/core';

import { RelacionDiagrama, EntidadDiagrama } from '../interfaces/diagrama.interface';
import { TipoRelacionUML, PosicionEditor } from '../interfaces/whiteboard-ui.interface';
import { WhiteboardEntityService } from './whiteboard-entity.service';

const ALTO_HEADER         = 36;
const ALTO_BOTON_AGREGAR  = 26;
const ANCHO_MINIMO_TABLA  = 220;

export interface EventoCardinalidadDatos {
  relacionId: number;
  extremo: 'origen' | 'destino';
  valorActual: string;
  pos: { x: number; y: number };
}

@Injectable()
export class WhiteboardRelationshipService {
  private readonly entityService = inject(WhiteboardEntityService);

  private graph: joint.dia.Graph | null = null;
  private paper: joint.dia.Paper | null = null;

  private linksRelaciones           = new Map<number, joint.dia.Link>();
  private relacionesMap             = new Map<number, RelacionDiagrama>();
  private relacionesPendientes: RelacionDiagrama[] = [];
  private conectoresClaseAsociacion = new Map<number, joint.dia.Link>();

  private enlacePendiente: joint.dia.Link | null = null;
  private relacionPendiente: {
    origenId: number;
    destinoId: number;
    puertoOrigen?: string;
    puertoDestino?: string;
  } | null = null;
  private enlaceSeleccionadoId: string | number | null = null;
  private capsulaSeleccionada: { relacionId: number; extremo: 'origen' | 'destino' } | null = null;
  private modoOscuro = false;

  public conectar(graph: joint.dia.Graph, paper: joint.dia.Paper): void {
    this.graph = graph;
    this.paper = paper;
  }

  public desconectar(): void {
    this.limpiar();
    this.graph = null;
    this.paper = null;
  }

  public limpiar(): void {
    this.conectoresClaseAsociacion.forEach(link => link.remove());
    this.conectoresClaseAsociacion.clear();
    this.linksRelaciones.forEach(link => link.remove());
    this.linksRelaciones.clear();
    this.relacionesMap.clear();
    this.relacionesPendientes = [];
    this.enlacePendiente = null;
    this.relacionPendiente = null;
    this.enlaceSeleccionadoId = null;
    this.capsulaSeleccionada = null;
  }

  // ── Verificación y Enlaces Pendientes ──

  public setRelacionPendiente(
    link: joint.dia.Link,
    origenId: number,
    destinoId: number,
    puertoOrigen?: string,
    puertoDestino?: string
  ): void {
    this.enlacePendiente = link;
    this.relacionPendiente = { origenId, destinoId, puertoOrigen, puertoDestino };
  }

  public cancelarRelacionPendiente(): void {
    if (this.enlacePendiente) {
      this.enlacePendiente.remove();
      this.enlacePendiente = null;
    }
    this.relacionPendiente = null;
  }

  public yaExisteRelacion(origenId: number, destinoId: number, ignorarRelacionId?: number): boolean {
    return Array.from(this.relacionesMap.values()).some(
      r => (ignorarRelacionId === undefined || r.id !== ignorarRelacionId) &&
           ((r.entidad_origen_id === origenId && r.entidad_destino_id === destinoId) ||
            (r.entidad_origen_id === destinoId && r.entidad_destino_id === origenId))
    );
  }

  public getRelacionIdPorLinkId(linkId: string | number): number | null {
    for (const [id, link] of this.linksRelaciones.entries()) {
      if (link.id === linkId) return id;
    }
    return null;
  }

  public getLinkPorId(linkId: string | number): joint.dia.Link | null {
    for (const link of this.linksRelaciones.values()) {
      if (link.id === linkId) return link;
    }
    return null;
  }

  public obtenerDireccionPuerto(puertoId?: string | null): 'top' | 'bottom' | 'left' | 'right' | null {
    if (!puertoId) return null;
    if (puertoId.startsWith('top')) return 'top';
    if (puertoId.startsWith('bottom')) return 'bottom';
    if (puertoId.startsWith('left')) return 'left';
    if (puertoId.startsWith('right')) return 'right';
    return null;
  }

  public obtenerOpcionesRouterManhattan(
    esAutoreferencia: boolean,
    puertoOrigen?: string | null,
    puertoDestino?: string | null
  ): {
    step: number;
    padding: number;
    maxAllowedDirectionChange: number;
    perpendicular: boolean;
    startDirections?: Array<'top' | 'bottom' | 'left' | 'right'>;
    endDirections?: Array<'top' | 'bottom' | 'left' | 'right'>;
  } {
    if (!esAutoreferencia) {
      return {
        step: 10,
        padding: 20,
        maxAllowedDirectionChange: 90,
        perpendicular: true
      };
    }

    const dirOrigen = this.obtenerDireccionPuerto(puertoOrigen) || 'right';
    const dirDestino = this.obtenerDireccionPuerto(puertoDestino) || 'top';

    return {
      step: 10,
      padding: 30, // Aléjate de la tabla 30px antes de doblar
      maxAllowedDirectionChange: 90,
      perpendicular: true,
      startDirections: [dirOrigen],
      endDirections: [dirDestino]
    };
  }

  // ── Estilo y Marcadores UML ──

  public aplicarEstiloRelacion(link: joint.dia.Link, tipo: RelacionDiagrama['tipo'], modoOscuro: boolean, _esClaseAsociacion = false): void {
    const colorLinea = modoOscuro ? '#EDEDED' : '#222222';
    const colorFondo = modoOscuro ? '#111111' : '#FFFFFF';

    link.attr('line/stroke', colorLinea);
    link.attr('line/strokeWidth', 1.8);
    link.attr('line/strokeDasharray', 'none');

    switch (tipo) {
      case 'asociacion':
        link.attr('line/sourceMarker', { type: 'none' });
        link.attr('line/targetMarker', { type: 'none' });
        break;

      case 'agregacion':
        link.attr('line/sourceMarker', {
          type: 'path',
          d: 'M 0 0 10 -6 20 0 10 6 z',
          fill: colorFondo,
          stroke: colorLinea,
          strokeWidth: 1.8
        });
        link.attr('line/targetMarker', { type: 'none' });
        break;

      case 'composicion':
        link.attr('line/sourceMarker', {
          type: 'path',
          d: 'M 0 0 10 -6 20 0 10 6 z',
          fill: colorLinea,
          stroke: colorLinea,
          strokeWidth: 1.8
        });
        link.attr('line/targetMarker', { type: 'none' });
        break;

      case 'herencia':
        link.attr('line/sourceMarker', { type: 'none' });
        link.attr('line/targetMarker', {
          type: 'path',
          d: 'M 14 -8 0 0 14 8 z',
          fill: colorFondo,
          stroke: colorLinea,
          strokeWidth: 1.8
        });
        break;
    }
  }

  public esOrigenBloqueado(relacion: RelacionDiagrama | undefined | null): boolean {
    if (!relacion) return false;
    if (relacion.tipo === 'composicion') return true;
    if (relacion.origen_bloqueado) return true;
    return false;
  }

  // ── Confirmar y Renderizar Relaciones ──

  public confirmarTipoRelacion(
    tipo: TipoRelacionUML,
    nuevoRelacionId: number,
    nuevoRelacionId2: number | undefined,
    nuevoClaseAsocEntidadId: number | undefined,
    modoOscuro: boolean
  ): { relaciones: RelacionDiagrama[]; entidadIntermedia?: EntidadDiagrama } | null {
    if (!this.enlacePendiente || !this.relacionPendiente) {
      this.cancelarRelacionPendiente();
      return null;
    }

    const { origenId, destinoId, puertoOrigen, puertoDestino } = this.relacionPendiente;
    const link = this.enlacePendiente;

    if (tipo === 'clase_asociacion') {
      return this.ejecutarMacroClaseAsociacion(
        origenId,
        destinoId,
        link,
        nuevoRelacionId,
        nuevoRelacionId2 || (nuevoRelacionId - 1),
        nuevoClaseAsocEntidadId || (nuevoRelacionId - 2),
        modoOscuro,
        puertoOrigen,
        puertoDestino
      );
    }

    const esAutoreferencia = origenId === destinoId;
    link.router('manhattan', this.obtenerOpcionesRouterManhattan(esAutoreferencia, puertoOrigen, puertoDestino));

    this.aplicarEstiloRelacion(link, tipo, modoOscuro);

    let cardOrigen = '';
    let cardDestino = '';

    switch (tipo) {
      case 'asociacion':
      case 'agregacion':
      case 'composicion':
        cardOrigen = '1';
        cardDestino = '0..*';
        break;
      case 'herencia':
        cardOrigen = '';
        cardDestino = '';
        break;
    }

    const esBloqueado = tipo === 'composicion';

    const nuevaRelacion: RelacionDiagrama = {
      id: nuevoRelacionId,
      nombre_relacion: '',
      tipo,
      entidad_origen_id: origenId,
      entidad_destino_id: destinoId,
      puerto_origen: puertoOrigen,
      puerto_destino: puertoDestino,
      cardinalidad_origen: cardOrigen,
      cardinalidad_destino: cardDestino,
      origen_bloqueado: esBloqueado,
      vertices: []
    };

    this.actualizarEtiquetasCardinalidad(link, nuevaRelacion, modoOscuro);

    this.relacionesMap.set(nuevaRelacion.id, nuevaRelacion);
    this.linksRelaciones.set(nuevaRelacion.id, link);

    this.enlacePendiente = null;
    this.relacionPendiente = null;

    return { relaciones: [nuevaRelacion] };
  }

  private encontrarPosicionLibreClaseAsociacion(
    ancho: number,
    alto: number,
    celdaOrigen: joint.dia.Element,
    celdaDestino: joint.dia.Element,
    esAutoreferencia: boolean
  ): { x: number; y: number } {
    if (!this.graph) {
      return { x: 100, y: 100 };
    }

    const PADDING_SEGURIDAD = 24;
    const bboxes = this.graph.getElements().map(el => el.getBBox().clone().inflate(PADDING_SEGURIDAD, PADDING_SEGURIDAD));

    const bboxOrigen = celdaOrigen.getBBox();
    const bboxDestino = celdaDestino.getBBox();

    let centroReferencia: joint.g.Point;
    if (esAutoreferencia) {
      centroReferencia = new joint.g.Point(bboxOrigen.x + bboxOrigen.width + 80, bboxOrigen.y - 40);
    } else {
      const cO = bboxOrigen.center();
      const cD = bboxDestino.center();
      centroReferencia = new joint.g.Point((cO.x + cD.x) / 2, (cO.y + cD.y) / 2);
    }

    // Probar candidatos concéntricos alrededor de centroReferencia
    const radios = [70, 130, 190, 260, 340, 420];
    const angulos = [
      -Math.PI / 2, // Arriba
      Math.PI / 2,  // Abajo
      0,            // Derecha
      Math.PI,      // Izquierda
      -Math.PI / 4, // Arriba-derecha
      -3 * Math.PI / 4, // Arriba-izquierda
      Math.PI / 4,  // Abajo-derecha
      3 * Math.PI / 4   // Abajo-izquierda
    ];

    for (const r of radios) {
      for (const ang of angulos) {
        const cx = centroReferencia.x + Math.cos(ang) * (r + (Math.abs(Math.cos(ang)) * ancho / 2));
        const cy = centroReferencia.y + Math.sin(ang) * (r + (Math.abs(Math.sin(ang)) * alto / 2));

        const candX = Math.round(cx - ancho / 2);
        const candY = Math.round(cy - alto / 2);

        if (candX < 24 || candY < 24) continue;

        const candidatoRect = new joint.g.Rect(candX, candY, ancho, alto);

        let solapa = false;
        for (const bbox of bboxes) {
          if (candidatoRect.intersect(bbox)) {
            solapa = true;
            break;
          }
        }

        if (!solapa) {
          return { x: candX, y: candY };
        }
      }
    }

    // Fallback seguro
    const fbX = Math.max(24, Math.round(centroReferencia.x - ancho / 2));
    const fbY = Math.max(24, Math.round(centroReferencia.y - alto - 80));
    return { x: fbX, y: fbY };
  }

  private ejecutarMacroClaseAsociacion(
    origenId: number,
    destinoId: number,
    linkPrincipal: joint.dia.Link,
    nuevoRelacionId: number,
    _nuevoRelacionId2: number,
    nuevoClaseAsocEntidadId: number | undefined,
    modoOscuro: boolean,
    puertoOrigen?: string,
    puertoDestino?: string
  ): { relaciones: RelacionDiagrama[]; entidadIntermedia: EntidadDiagrama } | null {
    this.enlacePendiente = null;
    this.relacionPendiente = null;

    const entidadOrigen = this.entityService.getEntidad(origenId);
    const entidadDestino = this.entityService.getEntidad(destinoId);
    if (!entidadOrigen || !entidadDestino || !this.graph) {
      linkPrincipal.remove();
      return null;
    }

    const celdaOrigen = this.entityService.getCelda(origenId);
    const celdaDestino = this.entityService.getCelda(destinoId);
    if (!celdaOrigen || !celdaDestino) {
      linkPrincipal.remove();
      return null;
    }

    const esAutoreferencia = origenId === destinoId;

    const nombreOrigen = (entidadOrigen.nombre || 'Origen').trim().replace(/\s+/g, '_');
    const nombreDestino = (entidadDestino.nombre || 'Destino').trim().replace(/\s+/g, '_');
    const nombreIntermedio = esAutoreferencia
      ? `${nombreOrigen.toLowerCase()}_relacion`
      : `${nombreOrigen.toLowerCase()}_${nombreDestino.toLowerCase()}`;

    const anchoIntermedio = Math.max(
      ANCHO_MINIMO_TABLA,
      this.entityService.medirAnchoTexto(nombreIntermedio, '700 13px "JetBrains Mono", monospace') + 56
    );
    const altoIntermedio = ALTO_HEADER + ALTO_BOTON_AGREGAR + 14;

    // Calcular posición libre más cercana usando bounding boxes nativas de JointJS (joint.g.Rect)
    const { x: coordX, y: coordY } = this.encontrarPosicionLibreClaseAsociacion(
      anchoIntermedio,
      altoIntermedio,
      celdaOrigen,
      celdaDestino,
      esAutoreferencia
    );

    const entidadIntermedia = this.entityService.crearEntidadLocal(
      coordX,
      coordY,
      nuevoClaseAsocEntidadId || -Date.now(),
      modoOscuro ? {
        lienzo: '#111111', grid: 'rgba(255,255,255,0.04)', entidadFondo: '#1A1A1A', entidadBorde: 'rgba(255,255,255,0.18)',
        headerFondo: '#1E293B', headerBorde: '#334155', headerTexto: '#F8FAFC', bodyTexto: '#AAAAAA', bloqueadoBorde: '#F59E0B'
      } : {
        lienzo: '#FFFFFF', grid: 'rgba(0,0,0,0.06)', entidadFondo: '#FAFAFA', entidadBorde: 'rgba(0,0,0,0.18)',
        headerFondo: '#1E293B', headerBorde: '#334155', headerTexto: '#F8FAFC', bodyTexto: '#333333', bloqueadoBorde: '#F59E0B'
      }
    );
    entidadIntermedia.nombre = nombreIntermedio;
    entidadIntermedia.es_intermedia = true;
    this.entityService.actualizarCeldaVisual(
      entidadIntermedia,
      modoOscuro ? {
        lienzo: '#111111', grid: 'rgba(255,255,255,0.04)', entidadFondo: '#1A1A1A', entidadBorde: 'rgba(255,255,255,0.18)',
        headerFondo: '#1E293B', headerBorde: '#334155', headerTexto: '#F8FAFC', bodyTexto: '#AAAAAA', bloqueadoBorde: '#F59E0B'
      } : {
        lienzo: '#FFFFFF', grid: 'rgba(0,0,0,0.06)', entidadFondo: '#FAFAFA', entidadBorde: 'rgba(0,0,0,0.18)',
        headerFondo: '#1E293B', headerBorde: '#334155', headerTexto: '#F8FAFC', bodyTexto: '#333333', bloqueadoBorde: '#F59E0B'
      }
    );

    // 1. Enlace Principal (Sólido): Una asociación normal y continua que va directamente de cliente a usuario
    linkPrincipal.router('manhattan', this.obtenerOpcionesRouterManhattan(esAutoreferencia, puertoOrigen, puertoDestino));
    this.aplicarEstiloRelacion(linkPrincipal, 'asociacion', modoOscuro, true);

    const relacionPrincipal: RelacionDiagrama = {
      id: nuevoRelacionId,
      nombre_relacion: '',
      tipo: 'asociacion',
      entidad_origen_id: origenId,
      entidad_destino_id: destinoId,
      puerto_origen: puertoOrigen,
      puerto_destino: puertoDestino,
      cardinalidad_origen: '0..*',
      cardinalidad_destino: '0..*',
      clase_asociacion_id: entidadIntermedia.id,
      origen_bloqueado: false,
      vertices: []
    };

    this.actualizarEtiquetasCardinalidad(linkPrincipal, relacionPrincipal, modoOscuro);
    this.relacionesMap.set(relacionPrincipal.id, relacionPrincipal);
    this.linksRelaciones.set(relacionPrincipal.id, linkPrincipal);

    // 2. Enlace Secundario (Punteado): Una línea que nace en la caja cliente_usuario y cuyo destino es el Enlace Principal
    this.crearConectorClaseAsociacion(relacionPrincipal.id, entidadIntermedia.id, modoOscuro);

    return { relaciones: [relacionPrincipal], entidadIntermedia };
  }

  public crearConectorClaseAsociacion(relacionId: number, claseAsociacionId: number, modoOscuro: boolean): void {
    if (!this.graph) return;

    const linkPrincipal = this.linksRelaciones.get(relacionId);
    const celdaIntermedia = this.entityService.getCelda(claseAsociacionId);

    if (!linkPrincipal || !celdaIntermedia) return;

    const conectorExistente = this.conectoresClaseAsociacion.get(relacionId);
    if (conectorExistente) {
      conectorExistente.remove();
      this.conectoresClaseAsociacion.delete(relacionId);
    }

    const colorLinea = modoOscuro ? '#EDEDED' : '#222222';

    const linkConector = new joint.shapes.standard.Link({
      source: { id: celdaIntermedia.id },
      target: {
        id: linkPrincipal.id,
        anchor: { name: 'connectionRatio', args: { ratio: 0.5 } }
      },
      router: { name: 'normal' },
      attrs: {
        line: {
          stroke: colorLinea,
          strokeWidth: 1.5,
          strokeDasharray: '5,5',
          sourceMarker: { type: 'none' },
          targetMarker: { type: 'none' },
          pointerEvents: 'none'
        }
      },
      interactive: false
    });

    this.graph.addCell(linkConector);
    this.conectoresClaseAsociacion.set(relacionId, linkConector);
  }

  public renderizarRelaciones(relaciones: RelacionDiagrama[], modoOscuro: boolean): void {
    if (!relaciones) return;
    this.conectoresClaseAsociacion.forEach(link => link.remove());
    this.conectoresClaseAsociacion.clear();
    this.linksRelaciones.forEach(link => link.remove());
    this.linksRelaciones.clear();
    this.relacionesMap.clear();

    relaciones.forEach(r => {
      this.crearRelacionRemota(r, modoOscuro);
    });
  }

  public crearRelacionRemota(relacion: RelacionDiagrama, modoOscuro: boolean): void {
    if (!this.graph || this.relacionesMap.has(relacion.id)) return;

    const celdaOrigen = this.entityService.getCelda(relacion.entidad_origen_id);
    const celdaDestino = this.entityService.getCelda(relacion.entidad_destino_id);

    if (!celdaOrigen || !celdaDestino) {
      if (!this.relacionesPendientes.some(r => r.id === relacion.id)) {
        this.relacionesPendientes.push(relacion);
      }
      return;
    }

    if (relacion.tipo === 'composicion') {
      relacion.origen_bloqueado = true;
    }

    const esAutoreferencia = relacion.entidad_origen_id === relacion.entidad_destino_id;
    const link = new joint.shapes.standard.Link({
      source: {
        id: celdaOrigen.id,
        ...(relacion.puerto_origen ? { port: relacion.puerto_origen } : {})
      },
      target: {
        id: celdaDestino.id,
        ...(relacion.puerto_destino ? { port: relacion.puerto_destino } : {})
      },
      router: {
        name: 'manhattan',
        args: this.obtenerOpcionesRouterManhattan(esAutoreferencia, relacion.puerto_origen, relacion.puerto_destino)
      },
      connector: { name: 'rounded', args: { radius: 8 } }
    });

    this.aplicarEstiloRelacion(link, relacion.tipo, modoOscuro, !!relacion.clase_asociacion_id);
    this.actualizarEtiquetasCardinalidad(link, relacion, modoOscuro);
    this.graph.addCell(link);
    this.linksRelaciones.set(relacion.id, link);
    this.relacionesMap.set(relacion.id, relacion);

    if (relacion.clase_asociacion_id) {
      this.crearConectorClaseAsociacion(relacion.id, relacion.clase_asociacion_id, modoOscuro);
    }
  }

  public procesarRelacionesPendientes(modoOscuro: boolean): void {
    if (this.relacionesPendientes.length > 0) {
      const aProcesar = [...this.relacionesPendientes];
      this.relacionesPendientes = [];
      aProcesar.forEach(r => this.crearRelacionRemota(r, modoOscuro));
    }
    this.verificarConectoresClaseAsociacion(modoOscuro);
  }

  public verificarConectoresClaseAsociacion(modoOscuro: boolean): void {
    if (!this.graph) return;
    this.relacionesMap.forEach((rel, relId) => {
      if (rel.clase_asociacion_id && !this.conectoresClaseAsociacion.has(relId)) {
        this.crearConectorClaseAsociacion(relId, rel.clase_asociacion_id, modoOscuro);
      }
    });
  }

  public actualizarRelacionRemota(relacion: RelacionDiagrama, modoOscuro: boolean): void {
    if (!relacion) return;
    const numId = Number(relacion.id);
    const existente = this.relacionesMap.get(numId);
    if (existente) {
      if (relacion.cardinalidad_origen !== undefined) existente.cardinalidad_origen = relacion.cardinalidad_origen;
      if (relacion.cardinalidad_destino !== undefined) existente.cardinalidad_destino = relacion.cardinalidad_destino;
      if (relacion.origen_bloqueado !== undefined) existente.origen_bloqueado = relacion.origen_bloqueado;
      if (relacion.nombre_relacion !== undefined) existente.nombre_relacion = relacion.nombre_relacion;
      if (relacion.puerto_origen !== undefined) existente.puerto_origen = relacion.puerto_origen;
      if (relacion.puerto_destino !== undefined) existente.puerto_destino = relacion.puerto_destino;
      if (relacion.entidad_origen_id !== undefined) existente.entidad_origen_id = relacion.entidad_origen_id;
      if (relacion.entidad_destino_id !== undefined) existente.entidad_destino_id = relacion.entidad_destino_id;
    }
    const link = this.linksRelaciones.get(numId);
    if (link) {
      const origId = existente?.entidad_origen_id ?? relacion.entidad_origen_id;
      const destId = existente?.entidad_destino_id ?? relacion.entidad_destino_id;
      const celdaOrigen = this.entityService.getCelda(origId);
      const celdaDestino = this.entityService.getCelda(destId);

      const puertoOrigen = existente?.puerto_origen ?? relacion.puerto_origen;
      const puertoDestino = existente?.puerto_destino ?? relacion.puerto_destino;

      if (celdaOrigen) {
        link.source({
          id: celdaOrigen.id,
          ...(puertoOrigen ? { port: puertoOrigen } : {})
        });
      }
      if (celdaDestino) {
        link.target({
          id: celdaDestino.id,
          ...(puertoDestino ? { port: puertoDestino } : {})
        });
      }

      const esAutoreferencia = origId === destId;
      link.router('manhattan', this.obtenerOpcionesRouterManhattan(esAutoreferencia, puertoOrigen, puertoDestino));

      this.actualizarEtiquetasCardinalidad(link, existente || relacion, modoOscuro);

      const claseAsocId = existente?.clase_asociacion_id ?? relacion.clase_asociacion_id;
      if (claseAsocId) {
        this.crearConectorClaseAsociacion(numId, claseAsocId, modoOscuro);
      }
    }
  }

  public actualizarPuertosRelacion(
    relacionId: number,
    nuevoOrigenId: number,
    nuevoDestinoId: number,
    nuevoPuertoOrigen?: string,
    nuevoPuertoDestino?: string,
    modoOscuro: boolean = false
  ): RelacionDiagrama | null {
    const relacion = this.relacionesMap.get(relacionId);
    const link = this.linksRelaciones.get(relacionId);
    if (!relacion || !link) return null;

    relacion.entidad_origen_id = nuevoOrigenId;
    relacion.entidad_destino_id = nuevoDestinoId;
    relacion.puerto_origen = nuevoPuertoOrigen;
    relacion.puerto_destino = nuevoPuertoDestino;
    relacion.vertices = [];

    const celdaOrigen = this.entityService.getCelda(nuevoOrigenId);
    const celdaDestino = this.entityService.getCelda(nuevoDestinoId);
    if (!celdaOrigen || !celdaDestino) return null;

    link.source({
      id: celdaOrigen.id,
      ...(nuevoPuertoOrigen ? { port: nuevoPuertoOrigen } : {})
    });
    link.target({
      id: celdaDestino.id,
      ...(nuevoPuertoDestino ? { port: nuevoPuertoDestino } : {})
    });

    const esAutoreferencia = nuevoOrigenId === nuevoDestinoId;
    link.router('manhattan', this.obtenerOpcionesRouterManhattan(esAutoreferencia, nuevoPuertoOrigen, nuevoPuertoDestino));

    this.actualizarEtiquetasCardinalidad(link, relacion, modoOscuro);

    if (relacion.clase_asociacion_id) {
      this.crearConectorClaseAsociacion(relacion.id, relacion.clase_asociacion_id, modoOscuro);
    }

    return { ...relacion, vertices: [] };
  }

  public eliminarRelacionRemota(relacionId: number): void {
    const conector = this.conectoresClaseAsociacion.get(relacionId);
    if (conector) {
      conector.remove();
      this.conectoresClaseAsociacion.delete(relacionId);
    }

    const link = this.linksRelaciones.get(relacionId);
    if (link) {
      link.remove();
      this.linksRelaciones.delete(relacionId);
    }
    this.relacionesMap.delete(relacionId);
    if (this.enlaceSeleccionadoId === link?.id) {
      this.deseleccionarEnlace();
    }
  }

  public limpiarRelacionesDeEntidad(entidadId: number): void {
    this.relacionesMap.forEach((r, relId) => {
      if (r.clase_asociacion_id === entidadId) {
        r.clase_asociacion_id = null;
        const conector = this.conectoresClaseAsociacion.get(relId);
        if (conector) {
          conector.remove();
          this.conectoresClaseAsociacion.delete(relId);
        }
      }
    });

    const relsAEliminar: number[] = [];
    this.relacionesMap.forEach((r, relId) => {
      if (r.entidad_origen_id === entidadId || r.entidad_destino_id === entidadId) {
        relsAEliminar.push(relId);
      }
    });
    relsAEliminar.forEach(relId => this.eliminarRelacionRemota(relId));
  }

  // ── Herramientas de Enlaces y Vértices ──

  public esConectorAuxiliar(linkId: string | number): boolean {
    for (const conector of this.conectoresClaseAsociacion.values()) {
      if (conector.id === linkId) return true;
    }
    return false;
  }

  public mostrarHerramientasEnlace(linkView: joint.dia.LinkView): void {
    if (!linkView || !linkView.model) return;
    if (this.esConectorAuxiliar(linkView.model.id)) return;

    if (linkView.hasTools()) return;

    const fill = this.modoOscuro ? '#FFFFFF' : '#00A3FF';
    const stroke = this.modoOscuro ? '#18181B' : '#FFFFFF';

    const toolsView = new joint.dia.ToolsView({
      tools: [
        new joint.linkTools.SourceArrowhead({
          attributes: {
            d: 'M -4 0 a 4 4 0 1 0 8 0 a 4 4 0 1 0 -8 0 Z',
            fill: fill,
            stroke: stroke,
            'stroke-width': 1.8,
            cursor: 'grab',
            class: 'source-arrowhead'
          }
        }),
        new joint.linkTools.TargetArrowhead({
          attributes: {
            d: 'M -4 0 a 4 4 0 1 0 8 0 a 4 4 0 1 0 -8 0 Z',
            fill: fill,
            stroke: stroke,
            'stroke-width': 1.8,
            cursor: 'grab',
            class: 'target-arrowhead'
          }
        })
      ]
    });
    linkView.addTools(toolsView);
  }

  public ocultarHerramientasEnlace(linkView: joint.dia.LinkView, arrastrando = false): void {
    if (!linkView || !linkView.model) return;
    if (arrastrando) return;
    if (this.enlaceSeleccionadoId === linkView.model.id) return;
    linkView.removeTools();
  }

  public seleccionarEnlace(linkView: joint.dia.LinkView): void {
    if (!linkView || !linkView.model) return;
    if (this.esConectorAuxiliar(linkView.model.id)) return;

    if (this.enlaceSeleccionadoId && this.enlaceSeleccionadoId !== linkView.model.id) {
      this.deseleccionarEnlace();
    }

    this.enlaceSeleccionadoId = linkView.model.id;
    this.mostrarHerramientasEnlace(linkView);
  }

  public deseleccionarEnlace(): void {
    if (this.enlaceSeleccionadoId && this.paper) {
      const link = this.getLinkPorId(this.enlaceSeleccionadoId);
      if (link) {
        const linkView = link.findView(this.paper) as joint.dia.LinkView | null;
        if (linkView) {
          linkView.removeTools();
        }
      }
    }
    if (this.paper) {
      this.paper.removeTools();
    }
    this.enlaceSeleccionadoId = null;
  }

  public sincronizarVerticesEnlace(_link: joint.dia.Link): void {
  }

  // ── Badges y Píldoras de Cardinalidad ──

  public actualizarEtiquetasCardinalidad(link: joint.dia.Link, relacion: RelacionDiagrama, modoOscuro: boolean): void {
    if (!link || !relacion) return;

    if (relacion.tipo === 'herencia') {
      if (relacion.nombre_relacion && relacion.nombre_relacion.trim() !== '') {
        const fondoBadgeNormal = modoOscuro ? '#18181B' : '#FFFFFF';
        const textoColorNormal = modoOscuro ? '#EDEDED' : '#111111';
        link.labels([
          {
            attrs: {
              root: { class: 'etiqueta-nombre-relacion' },
              rect: {
                ref: 'text',
                fill: fondoBadgeNormal,
                stroke: 'transparent',
                strokeWidth: 0,
                rx: 4,
                ry: 4,
                x: 'calc(x - 6)',
                y: 'calc(y - 2)',
                width: 'calc(w + 12)',
                height: 'calc(h + 4)',
                cursor: 'pointer'
              },
              text: {
                text: relacion.nombre_relacion.trim(),
                fill: textoColorNormal,
                fontSize: 12,
                fontStyle: 'italic',
                fontFamily: '"JetBrains Mono", monospace',
                fontWeight: '500',
                textAnchor: 'middle',
                textVerticalAnchor: 'middle',
                cursor: 'pointer'
              }
            },
            position: { distance: 0.5, offset: 0 }
          }
        ]);
      } else {
        link.labels([]);
      }
      return;
    }

    const cardOrigen = (relacion.cardinalidad_origen !== undefined && relacion.cardinalidad_origen !== '')
      ? relacion.cardinalidad_origen.trim()
      : '1';
    const cardDestino = (relacion.cardinalidad_destino !== undefined && relacion.cardinalidad_destino !== '')
      ? relacion.cardinalidad_destino.trim()
      : '0..*';

    if (!relacion.cardinalidad_origen) relacion.cardinalidad_origen = cardOrigen;
    if (!relacion.cardinalidad_destino) relacion.cardinalidad_destino = cardDestino;

    const esBloqueado = this.esOrigenBloqueado(relacion);
    const esOrigenSel = this.capsulaSeleccionada?.relacionId === relacion.id && this.capsulaSeleccionada?.extremo === 'origen';
    const esDestinoSel = this.capsulaSeleccionada?.relacionId === relacion.id && this.capsulaSeleccionada?.extremo === 'destino';

    const fondoBadgeNormal = modoOscuro ? '#18181B' : '#FFFFFF';
    const fondoBadgeSel = modoOscuro ? '#0B2545' : '#E0F2FE';
    const bordeBadgeNormal = modoOscuro ? 'rgba(255, 255, 255, 0.22)' : 'rgba(0, 0, 0, 0.20)';
    const textoColorNormal = modoOscuro ? '#EDEDED' : '#111111';
    const textoColorBloqueado = modoOscuro ? '#888888' : '#777777';

    const origenClases = 'capsula-cardinalidad' +
      (esOrigenSel ? ' capsula-seleccionada' : '') +
      (esBloqueado ? ' capsula-bloqueada' : '');

    const labels: joint.dia.Link.Label[] = [
      {
        attrs: {
          root: { class: origenClases },
          rect: {
            ref: 'text',
            fill: esOrigenSel ? fondoBadgeSel : fondoBadgeNormal,
            stroke: esOrigenSel ? '#00A3FF' : bordeBadgeNormal,
            strokeWidth: esOrigenSel ? 2 : 1.2,
            rx: 5,
            ry: 5,
            x: 'calc(x - 6)',
            y: 'calc(y - 3)',
            width: 'calc(w + 12)',
            height: 'calc(h + 6)',
            cursor: esBloqueado ? 'not-allowed' : 'pointer'
          },
          text: {
            text: cardOrigen,
            fill: esOrigenSel ? '#00A3FF' : (esBloqueado ? textoColorBloqueado : textoColorNormal),
            fontSize: 11,
            fontFamily: '"JetBrains Mono", monospace',
            fontWeight: esOrigenSel ? '700' : '600',
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            cursor: esBloqueado ? 'not-allowed' : 'pointer'
          }
        },
        position: { distance: 38, offset: 0 }
      },
      {
        attrs: {
          root: { class: 'capsula-cardinalidad' + (esDestinoSel ? ' capsula-seleccionada' : '') },
          rect: {
            ref: 'text',
            fill: esDestinoSel ? fondoBadgeSel : fondoBadgeNormal,
            stroke: esDestinoSel ? '#00A3FF' : bordeBadgeNormal,
            strokeWidth: esDestinoSel ? 2 : 1.2,
            rx: 5,
            ry: 5,
            x: 'calc(x - 6)',
            y: 'calc(y - 3)',
            width: 'calc(w + 12)',
            height: 'calc(h + 6)',
            cursor: 'pointer'
          },
          text: {
            text: cardDestino,
            fill: esDestinoSel ? '#00A3FF' : textoColorNormal,
            fontSize: 11,
            fontFamily: '"JetBrains Mono", monospace',
            fontWeight: esDestinoSel ? '700' : '600',
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            cursor: 'pointer'
          }
        },
        position: { distance: -38, offset: 0 }
      }
    ];

    if (relacion.nombre_relacion && relacion.nombre_relacion.trim() !== '') {
      labels.push({
        attrs: {
          root: { class: 'etiqueta-nombre-relacion' },
          rect: {
            ref: 'text',
            fill: fondoBadgeNormal,
            stroke: 'transparent',
            strokeWidth: 0,
            rx: 4,
            ry: 4,
            x: 'calc(x - 6)',
            y: 'calc(y - 2)',
            width: 'calc(w + 12)',
            height: 'calc(h + 4)',
            cursor: 'pointer'
          },
          text: {
            text: relacion.nombre_relacion.trim(),
            fill: textoColorNormal,
            fontSize: 12,
            fontStyle: 'italic',
            fontFamily: '"JetBrains Mono", monospace',
            fontWeight: '500',
            textAnchor: 'middle',
            textVerticalAnchor: 'middle',
            cursor: 'pointer'
          }
        },
        position: { distance: 0.5, offset: 0 }
      });
    }

    link.labels(labels);

    const linkView = link.findView(this.paper!) as joint.dia.LinkView | null;
    if (linkView) {
      const labelsNode = (linkView as unknown as { _V?: { labels?: { node?: Element } } })._V?.labels?.node || linkView.el.querySelector('.labels');
      if (labelsNode && labelsNode.parentNode === linkView.el) {
        linkView.el.appendChild(labelsNode);
      }
    }
  }

  public seleccionarCapsula(
    relacionId: number,
    extremo: 'origen' | 'destino',
    modoOscuro: boolean,
    labelG?: SVGGraphicsElement | null,
    container?: HTMLElement
  ): EventoCardinalidadDatos | null {
    const relacion = this.relacionesMap.get(relacionId);
    if (!relacion) return null;

    if (extremo === 'origen' && this.esOrigenBloqueado(relacion)) {
      return null;
    }

    this.deseleccionarEnlace();

    const previa = this.capsulaSeleccionada;
    this.capsulaSeleccionada = { relacionId, extremo };

    if (previa && previa.relacionId !== relacionId) {
      const relPrevia = this.relacionesMap.get(previa.relacionId);
      const linkPrevio = this.linksRelaciones.get(previa.relacionId);
      if (relPrevia && linkPrevio) {
        this.actualizarEtiquetasCardinalidad(linkPrevio, relPrevia, modoOscuro);
      }
    }

    const link = this.linksRelaciones.get(relacionId);
    if (link) {
      this.actualizarEtiquetasCardinalidad(link, relacion, modoOscuro);
    }

    const labelIdx = extremo === 'origen' ? 0 : 1;
    let targetG = labelG;
    if (link && this.paper) {
      const linkView = link.findView(this.paper) as joint.dia.LinkView | null;
      if (linkView) {
        const foundG = linkView.el.querySelector(`g[label-idx="${labelIdx}"]`) as SVGGraphicsElement | null;
        if (foundG) targetG = foundG;
      }
    }

    if (link && targetG && container) {
      const wrapperRect = container.parentElement!.getBoundingClientRect();
      const bbox = targetG.getBoundingClientRect();
      const menuAncho = 230;
      const menuAlto = 135;

      const posX = bbox.left - wrapperRect.left + bbox.width / 2;
      let posY = bbox.bottom - wrapperRect.top + 8;
      if (posY + menuAlto > wrapperRect.height - 16) {
        posY = Math.max(16, bbox.top - wrapperRect.top - menuAlto - 8);
      }

      const valorActual = extremo === 'origen' ? relacion.cardinalidad_origen : relacion.cardinalidad_destino;

      return {
        relacionId,
        extremo,
        valorActual: valorActual || '',
        pos: {
          x: Math.max(menuAncho / 2 + 16, Math.min(posX, wrapperRect.width - menuAncho / 2 - 16)),
          y: posY
        }
      };
    }
    return null;
  }

  public deseleccionarCapsula(modoOscuro: boolean): void {
    if (!this.capsulaSeleccionada) return;
    const previa = this.capsulaSeleccionada;
    this.capsulaSeleccionada = null;

    const rel = this.relacionesMap.get(previa.relacionId);
    const link = this.linksRelaciones.get(previa.relacionId);
    if (rel && link) {
      this.actualizarEtiquetasCardinalidad(link, rel, modoOscuro);
    }
  }

  public aplicarCardinalidad(relacionId: number, extremo: 'origen' | 'destino', valor: string, modoOscuro: boolean): RelacionDiagrama | null {
    const rel = this.relacionesMap.get(relacionId);
    const link = this.linksRelaciones.get(relacionId);

    if (rel && link) {
      if (extremo === 'origen' && this.esOrigenBloqueado(rel)) {
        return null;
      }
      if (extremo === 'origen') {
        rel.cardinalidad_origen = valor;
      } else {
        rel.cardinalidad_destino = valor;
      }
      rel.vertices = [];
      this.deseleccionarCapsula(modoOscuro);
      this.actualizarEtiquetasCardinalidad(link, rel, modoOscuro);
      return { ...rel, vertices: [] };
    }
    return null;
  }

  public actualizarNombreRelacion(relacionId: number, nombre: string, modoOscuro: boolean): RelacionDiagrama | null {
    const rel = this.relacionesMap.get(relacionId);
    const link = this.linksRelaciones.get(relacionId);
    if (rel && link) {
      rel.nombre_relacion = nombre;
      rel.vertices = [];
      this.actualizarEtiquetasCardinalidad(link, rel, modoOscuro);
      return { ...rel, vertices: [] };
    }
    return null;
  }

  public actualizarPropiedadesRelacion(
    relacionId: number,
    nombre: string,
    cardinalidadOrigen: string,
    cardinalidadDestino: string,
    modoOscuro: boolean
  ): RelacionDiagrama | null {
    const rel = this.relacionesMap.get(relacionId);
    const link = this.linksRelaciones.get(relacionId);
    if (rel && link) {
      rel.nombre_relacion = nombre;
      if (!this.esOrigenBloqueado(rel)) {
        rel.cardinalidad_origen = cardinalidadOrigen;
      }
      rel.cardinalidad_destino = cardinalidadDestino;
      rel.vertices = [];
      this.deseleccionarCapsula(modoOscuro);
      this.actualizarEtiquetasCardinalidad(link, rel, modoOscuro);
      return { ...rel, vertices: [] };
    }
    return null;
  }

  public getRelacion(relacionId: number): RelacionDiagrama | undefined {
    return this.relacionesMap.get(relacionId);
  }

  public obtenerPosicionEditorNombreRelacion(relacionId: number, container: HTMLElement): PosicionEditor | null {
    const link = this.linksRelaciones.get(relacionId);
    if (!link || !this.paper || !container) return null;

    const linkView = link.findView(this.paper) as joint.dia.LinkView | null;
    if (!linkView) return null;

    const wrapperRect = container.parentElement!.getBoundingClientRect();

    // 1. Si ya existe el elemento DOM de la etiqueta (.etiqueta-nombre-relacion), usar su bounding box
    const labelEl = linkView.el.querySelector('.etiqueta-nombre-relacion') as SVGGraphicsElement | null;
    if (labelEl) {
      const bbox = labelEl.getBoundingClientRect();
      const w = Math.max(130, Math.round(bbox.width) + 24);
      const h = Math.max(28, Math.round(bbox.height) + 6);
      const x = Math.round(bbox.left - wrapperRect.left - (w - bbox.width) / 2);
      const y = Math.round(bbox.top - wrapperRect.top - (h - bbox.height) / 2);
      return { x, y, w, h };
    }

    // 2. Si todavía no tiene etiqueta dibujada, calcular el punto medio del trazado ortogonal
    try {
      const point = linkView.getPointAtRatio(0.5);
      if (point) {
        const clientRect = this.paper.localToClientRect(point.x - 65, point.y - 14, 130, 28);
        const w = Math.max(120, Math.round(clientRect.width));
        const h = Math.max(26, Math.round(clientRect.height));
        const x = Math.round(clientRect.x - wrapperRect.left);
        const y = Math.round(clientRect.y - wrapperRect.top);
        return { x, y, w, h };
      }
    } catch {
      // Fallback si la conexión aún no está lista
    }

    return null;
  }

  public aplicarTema(modoOscuro: boolean): void {
    this.modoOscuro = modoOscuro;
    this.linksRelaciones.forEach((link, relId) => {
      const r = this.relacionesMap.get(relId);
      if (r) {
        this.aplicarEstiloRelacion(link, r.tipo, modoOscuro, !!r.clase_asociacion_id);
        this.actualizarEtiquetasCardinalidad(link, r, modoOscuro);
      }
    });

    const colorConector = modoOscuro ? '#EDEDED' : '#222222';
    this.conectoresClaseAsociacion.forEach(conector => {
      conector.attr('line/stroke', colorConector);
    });
  }

  public getRelaciones(): RelacionDiagrama[] {
    return Array.from(this.relacionesMap.values()).map(rel => {
      rel.vertices = [];
      return { ...rel, vertices: [] };
    });
  }

  public remapIds(
    idMap?: Record<string | number, number>,
    relIdMap?: Record<string | number, number>
  ): void {
    if (idMap && Object.keys(idMap).length > 0) {
      this.relacionesMap.forEach(rel => {
        if (idMap[rel.entidad_origen_id] !== undefined) {
          rel.entidad_origen_id = idMap[rel.entidad_origen_id];
        }
        if (idMap[rel.entidad_destino_id] !== undefined) {
          rel.entidad_destino_id = idMap[rel.entidad_destino_id];
        }
        if (rel.clase_asociacion_id !== undefined && rel.clase_asociacion_id !== null && idMap[rel.clase_asociacion_id] !== undefined) {
          rel.clase_asociacion_id = idMap[rel.clase_asociacion_id];
        }
      });
    }

    if (relIdMap && Object.keys(relIdMap).length > 0) {
      for (const [oldRelIdStr, newRelId] of Object.entries(relIdMap)) {
        const oldRelId = Number(oldRelIdStr);
        if (oldRelId === newRelId) continue;

        const rel = this.relacionesMap.get(oldRelId);
        if (rel) {
          this.relacionesMap.delete(oldRelId);
          rel.id = newRelId;
          this.relacionesMap.set(newRelId, rel);
        }

        const link = this.linksRelaciones.get(oldRelId);
        if (link) {
          this.linksRelaciones.delete(oldRelId);
          this.linksRelaciones.set(newRelId, link);
        }

        const conector = this.conectoresClaseAsociacion.get(oldRelId);
        if (conector) {
          this.conectoresClaseAsociacion.delete(oldRelId);
          this.conectoresClaseAsociacion.set(newRelId, conector);
        }
      }
    }
  }
}
