import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  DiagramaIARespuesta,
  DiagramaGeneradoPayload,
  EntidadIARespuesta,
  AtributoIARespuesta,
  RelacionIARespuesta,
  ContextoDiagramaIA,
  DeltaInstruccionIARespuesta
} from '../interfaces/asistente-ia.interface';
import {
  EntidadDiagrama,
  RelacionDiagrama,
  AtributoDiagrama
} from '../interfaces/diagrama.interface';

interface SpeechRecognitionResultItem {
  transcript: string;
  confidence: number;
}
interface SpeechRecognitionResultList {
  readonly length: number;
  [index: number]: {
    readonly length: number;
    [index: number]: SpeechRecognitionResultItem;
    isFinal: boolean;
  };
}
interface SpeechRecognitionEventLike extends Event {
  results: SpeechRecognitionResultList;
}
interface SpeechRecognitionLike {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
}

const TIPOS_VALIDOS: AtributoDiagrama['tipo'][] = [
  'string',
  'integer',
  'long',
  'double',
  'boolean',
  'date'
];

const TIPOS_RELACION_VALIDOS: RelacionDiagrama['tipo'][] = [
  'asociacion',
  'agregacion',
  'composicion',
  'herencia'
];

const REGEX_CARDINALIDAD = /^([0-9]+|\*|[0-9]+\.\.([0-9]+|\*))$/;

@Injectable({
  providedIn: 'root'
})
export class AsistenteIaService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/asistente/generar-diagrama-imagen/`;
  private readonly urlInstruccion = `${environment.apiUrl}/asistente/ejecutar-instruccion/`;

  public readonly escuchandoVoz$ = new BehaviorSubject<boolean>(false);
  public readonly textoVozProvisional$ = new Subject<string>();
  public readonly textoVozFinal$ = new Subject<string>();
  public readonly errorVoz$ = new Subject<string>();

  private recognition: SpeechRecognitionLike | null = null;

  /**
   * Ejecuta una instrucción o comando atómico de modelado por texto o voz
   */
  public ejecutarInstruccion(
    instruccion: string,
    contexto: ContextoDiagramaIA
  ): Observable<DeltaInstruccionIARespuesta> {
    return this.http.post<DeltaInstruccionIARespuesta>(this.urlInstruccion, {
      instruccion: instruccion.trim(),
      contexto_diagrama: contexto
    });
  }

  /**
   * Comprueba si el navegador actual soporta Web Speech API de forma nativa
   */
  public soportaReconocimientoVoz(): boolean {
    if (typeof window === 'undefined') return false;
    const win = window as unknown as {
      SpeechRecognition?: new () => SpeechRecognitionLike;
      webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    };
    return Boolean(win.SpeechRecognition || win.webkitSpeechRecognition);
  }

  /**
   * Inicia la captura de voz por micrófono usando Web Speech API
   */
  public iniciarReconocimientoVoz(): void {
    if (!this.soportaReconocimientoVoz()) {
      this.errorVoz$.next('Tu navegador no soporta reconocimiento de voz nativo. Por favor escribe tu instrucción.');
      return;
    }

    try {
      const win = window as unknown as {
        SpeechRecognition?: new () => SpeechRecognitionLike;
        webkitSpeechRecognition?: new () => SpeechRecognitionLike;
      };
      const RecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;
      if (!RecognitionClass) return;

      this.detenerReconocimientoVoz();
      const rec = new RecognitionClass();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'es-ES';

      rec.onresult = (event: SpeechRecognitionEventLike) => {
        let textoParcial = '';
        let textoFinal = '';
        for (let i = 0; i < event.results.length; i++) {
          const res = event.results[i];
          if (res.isFinal) {
            textoFinal += res[0].transcript;
          } else {
            textoParcial += res[0].transcript;
          }
        }
        if (textoFinal.trim()) {
          this.textoVozFinal$.next(textoFinal.trim());
        } else if (textoParcial.trim()) {
          this.textoVozProvisional$.next(textoParcial.trim());
        }
      };

      rec.onerror = (ev: { error: string }) => {
        this.escuchandoVoz$.next(false);
        const err = ev.error === 'not-allowed'
          ? 'Permiso de micrófono denegado. Puedes escribir la instrucción directamente.'
          : `Error en micrófono: ${ev.error}`;
        this.errorVoz$.next(err);
      };

      rec.onend = () => {
        this.escuchandoVoz$.next(false);
      };

      this.recognition = rec;
      rec.start();
      this.escuchandoVoz$.next(true);
    } catch {
      this.escuchandoVoz$.next(false);
      this.errorVoz$.next('No se pudo acceder al micrófono. Escribe la instrucción directamente.');
    }
  }

  /**
   * Detiene la captura de voz
   */
  public detenerReconocimientoVoz(): void {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch {
        // Ignorar
      }
      this.recognition = null;
    }
    this.escuchandoVoz$.next(false);
  }

  /**
   * Envía la imagen del boceto y las instrucciones opcionales al backend de Django
   */
  public generarDiagramaDesdeImagen(
    imagen: Blob | File,
    instrucciones?: string
  ): Observable<DiagramaIARespuesta> {
    const formData = new FormData();
    formData.append('imagen', imagen, 'boceto.jpg');
    if (instrucciones && instrucciones.trim().length > 0) {
      formData.append('instrucciones', instrucciones.trim());
    }
    return this.http.post<DiagramaIARespuesta>(this.url, formData);
  }

  /**
   * Comprime y redimensiona una imagen en el cliente para acelerar la subida
   * Máximo 1600px de ancho/alto y calidad JPEG 0.82
   */
  public comprimirImagen(archivo: File, maxDimension = 1600, calidad = 0.82): Promise<Blob> {
    return new Promise((resolve, reject) => {
      // Si el archivo ya es muy liviano (menor a 600KB), se envía tal cual
      if (archivo.size <= 600 * 1024 && archivo.type === 'image/jpeg') {
        resolve(archivo);
        return;
      }

      const reader = new FileReader();
      reader.onload = (e: ProgressEvent<FileReader>) => {
        const resultado = e.target?.result;
        if (typeof resultado !== 'string') {
          reject(new Error('No se pudo leer el archivo como DataURL'));
          return;
        }

        const img = new Image();
        img.onload = () => {
          let ancho = img.width;
          let alto = img.height;

          if (ancho > maxDimension || alto > maxDimension) {
            if (ancho > alto) {
              alto = Math.round((alto * maxDimension) / ancho);
              ancho = maxDimension;
            } else {
              ancho = Math.round((ancho * maxDimension) / alto);
              alto = maxDimension;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = ancho;
          canvas.height = alto;
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            resolve(archivo);
            return;
          }

          ctx.drawImage(img, 0, 0, ancho, alto);
          canvas.toBlob(
            (blob) => {
              if (blob) {
                resolve(blob);
              } else {
                resolve(archivo);
              }
            },
            'image/jpeg',
            calidad
          );
        };
        img.onerror = () => reject(new Error('No se pudo cargar la imagen para compresión'));
        img.src = resultado;
      };
      reader.onerror = () => reject(new Error('Error al leer el archivo'));
      reader.readAsDataURL(archivo);
    });
  }

  /**
   * Normaliza el JSON devuelto por Gemini, completando atributos faltantes,
   * asignando IDs temporales negativos y ubicando las entidades en cascada diagonal simple
   */
  public normalizarRespuestaIA(
    respuesta: DiagramaIARespuesta,
    centroX = 140,
    centroY = 100
  ): DiagramaGeneradoPayload {
    const entidadesEntrantes = respuesta.entidades || [];
    const relacionesEntrantes = respuesta.relaciones || [];

    const mapaIds = new Map<string | number, number>();
    const mapaEntidadesPorNombre = new Map<string, number>();
    const baseTiempo = Date.now() % 1000000000;
    let contadorSecuencia = 1;

    // 1. Mapear identificadores de entidades entrantes a IDs temporales de cliente
    for (let i = 0; i < entidadesEntrantes.length; i++) {
      const ent = entidadesEntrantes[i];
      const idTemporal = -(baseTiempo * 100 + (contadorSecuencia++ % 100));
      if (ent.id !== undefined && ent.id !== null) {
        mapaIds.set(ent.id, idTemporal);
        mapaIds.set(String(ent.id), idTemporal);
      }
      if (ent.nombre) {
        mapaEntidadesPorNombre.set(ent.nombre.trim().toLowerCase(), idTemporal);
      }
    }

    const resolverEntidadId = (ref: unknown): number | null => {
      if (ref === undefined || ref === null || ref === '') return null;
      if (typeof ref === 'number' && mapaIds.has(ref)) return mapaIds.get(ref)!;
      if (typeof ref === 'string') {
        const num = Number(ref);
        if (!isNaN(num) && mapaIds.has(num)) return mapaIds.get(num)!;
        if (mapaIds.has(ref)) return mapaIds.get(ref)!;
        const norm = ref.trim().toLowerCase();
        if (mapaEntidadesPorNombre.has(norm)) return mapaEntidadesPorNombre.get(norm)!;
      }
      return null;
    };

    // 2. Normalizar entidades
    const entidadesNormalizadas: EntidadDiagrama[] = entidadesEntrantes.map(
      (ent: EntidadIARespuesta, index: number): EntidadDiagrama => {
        const idTemporal = resolverEntidadId(ent.id) ?? -(baseTiempo * 100 + (contadorSecuencia++ % 100));

        let coordX: number;
        let coordY: number;

        if (ent.pos_x !== undefined && ent.pos_y !== undefined) {
          coordX = Math.round(centroX + (ent.pos_x / 1000) * 1100);
          coordY = Math.round(centroY + (ent.pos_y / 1000) * 750);
        } else {
          // Cascada diagonal simple de fallback
          coordX = Math.round(centroX + index * 70);
          coordY = Math.round(centroY + index * 60);
        }

        const atributosNormalizados = this.normalizarAtributos(ent.atributos || []);

        return {
          id: idTemporal,
          nombre: (ent.nombre || `Entidad_${index + 1}`).trim().replace(/\s+/g, '_'),
          estado: 'activo',
          coord_x: coordX,
          coord_y: coordY,
          ancho: 200,
          es_intermedia: Boolean(ent.es_intermedia),
          pos_x: ent.pos_x,
          pos_y: ent.pos_y,
          atributos: atributosNormalizados
        };
      }
    );

    const entidadesMap = new Map<number, EntidadDiagrama>();
    for (const ent of entidadesNormalizadas) {
      entidadesMap.set(ent.id, ent);
    }

    const conteoPares = new Map<string, number>();
    const relacionesNormalizadas: RelacionDiagrama[] = [];
    const intermediasEnlazadas = new Set<number>();
    const indicesRelacionesOmitidas = new Set<number>();

    // 3. Manejar entidades que la IA marcó explícitamente como intermedias (es_intermedia === true)
    // Caso: Si la IA generó 2 relaciones directas convergentes hacia la tabla intermedia C (A -> C y B -> C),
    // se fusionan en una única asociación A <-> B con clase_asociacion_id: C.id
    const idIntermediasIA = new Set<number>();
    entidadesNormalizadas.forEach(e => {
      if (e.es_intermedia) idIntermediasIA.add(e.id);
    });

    if (idIntermediasIA.size > 0) {
      const conexionesPorIntermedia = new Map<number, { relIndex: number; rel: RelacionIARespuesta; otraEntidadId: number }[]>();
      for (let i = 0; i < relacionesEntrantes.length; i++) {
        const r = relacionesEntrantes[i];
        const origId = resolverEntidadId(r.entidad_origen_id);
        const destId = resolverEntidadId(r.entidad_destino_id);
        if (origId === null || destId === null || origId === destId) continue;

        if (idIntermediasIA.has(origId)) {
          if (!conexionesPorIntermedia.has(origId)) conexionesPorIntermedia.set(origId, []);
          conexionesPorIntermedia.get(origId)!.push({ relIndex: i, rel: r, otraEntidadId: destId });
        }
        if (idIntermediasIA.has(destId)) {
          if (!conexionesPorIntermedia.has(destId)) conexionesPorIntermedia.set(destId, []);
          conexionesPorIntermedia.get(destId)!.push({ relIndex: i, rel: r, otraEntidadId: origId });
        }
      }

      for (const entIntermediaId of idIntermediasIA) {
        const conexiones = conexionesPorIntermedia.get(entIntermediaId) || [];
        if (conexiones.length === 2 && conexiones[0].otraEntidadId !== conexiones[1].otraEntidadId) {
          const conn1 = conexiones[0];
          const conn2 = conexiones[1];
          const tempIdA = conn1.otraEntidadId;
          const tempIdB = conn2.otraEntidadId;

          indicesRelacionesOmitidas.add(conn1.relIndex);
          indicesRelacionesOmitidas.add(conn2.relIndex);

          const entIntermedia = entidadesMap.get(entIntermediaId);
          const entA = entidadesMap.get(tempIdA);
          const entB = entidadesMap.get(tempIdB);

          if (entIntermedia && entA && entB) {
            entIntermedia.es_intermedia = true;
            entIntermedia.coord_x = Math.round((entA.coord_x + entB.coord_x) / 2);
            entIntermedia.coord_y = Math.round(Math.min(entA.coord_y, entB.coord_y) - 100);
            if (entIntermedia.coord_y < 40) {
              entIntermedia.coord_y = Math.round((entA.coord_y + entB.coord_y) / 2 + 120);
            }
          }

          const idRelTemp = -(baseTiempo * 100 + (contadorSecuencia++ % 100));
          const puertos = this.calcularPuertosRelacion(tempIdA, tempIdB, entidadesMap, conteoPares);

          relacionesNormalizadas.push({
            id: idRelTemp,
            nombre_relacion: (conn1.rel.nombre_relacion || conn2.rel.nombre_relacion || '').trim(),
            tipo: 'asociacion',
            entidad_origen_id: tempIdA,
            entidad_destino_id: tempIdB,
            cardinalidad_origen: '0..*',
            cardinalidad_destino: '0..*',
            clase_asociacion_id: entIntermediaId,
            puerto_origen: puertos.origen,
            puerto_destino: puertos.destino,
            vertices: [],
            origen_bloqueado: false
          });

          intermediasEnlazadas.add(entIntermediaId);
        }
      }
    }

    // 4. Procesar el resto de relaciones recibidas
    for (let i = 0; i < relacionesEntrantes.length; i++) {
      if (indicesRelacionesOmitidas.has(i)) continue;

      const rel = relacionesEntrantes[i];
      const origIdReal = resolverEntidadId(rel.entidad_origen_id);
      const destIdReal = resolverEntidadId(rel.entidad_destino_id);

      if (origIdReal === null || destIdReal === null) continue;

      const idRelTemporal = -(baseTiempo * 100 + (contadorSecuencia++ % 100));
      let tipoRelacion = this.normalizarTipoRelacion(rel.tipo);
      let cardOrigen = this.normalizarCardinalidad(rel.cardinalidad_origen, '');
      let cardDestino = this.normalizarCardinalidad(rel.cardinalidad_destino, '');

      let claseAsocIdReal: number | null = null;
      if (rel.clase_asociacion_id !== undefined && rel.clase_asociacion_id !== null) {
        claseAsocIdReal = resolverEntidadId(rel.clase_asociacion_id);
      }

      const esMuchosAMuchos = (cardOrigen === '0..*' || cardOrigen === '*' || cardOrigen === '1..*') &&
        (cardDestino === '0..*' || cardDestino === '*' || cardDestino === '1..*');

      if (claseAsocIdReal !== null) {
        const entIntermedia = entidadesMap.get(claseAsocIdReal);
        if (entIntermedia) {
          entIntermedia.es_intermedia = true;
          intermediasEnlazadas.add(claseAsocIdReal);
        }
        tipoRelacion = 'asociacion';
        cardOrigen = '0..*';
        cardDestino = '0..*';
      } else if (esMuchosAMuchos) {
        // Relación directa de Muchos a Muchos sin clase de asociación explícita:
        // Buscar si hay alguna entidad intermedia huérfana no vinculada
        const entIntermediaHuerfana = entidadesNormalizadas.find(
          e => e.es_intermedia && !intermediasEnlazadas.has(e.id)
        );

        if (entIntermediaHuerfana) {
          claseAsocIdReal = entIntermediaHuerfana.id;
          intermediasEnlazadas.add(entIntermediaHuerfana.id);
        } else {
          // Si no existe, crear la entidad intermedia automáticamente
          const entOrig = entidadesMap.get(origIdReal);
          const entDest = entidadesMap.get(destIdReal);
          const nomOrig = (entOrig?.nombre || 'origen').toLowerCase().trim().replace(/\s+/g, '_');
          const nomDest = (entDest?.nombre || 'destino').toLowerCase().trim().replace(/\s+/g, '_');
          const nombreIntermedio = `${nomOrig}_${nomDest}`;

          const idIntermedio = -(baseTiempo * 100 + (contadorSecuencia++ % 100));
          const coordX = entOrig && entDest ? Math.round((entOrig.coord_x + entDest.coord_x) / 2) : centroX;
          const coordY = entOrig && entDest ? Math.round(Math.min(entOrig.coord_y, entDest.coord_y) - 100) : centroY;

          const entIntermedia: EntidadDiagrama = {
            id: idIntermedio,
            nombre: nombreIntermedio,
            estado: 'activo',
            coord_x: coordX,
            coord_y: Math.max(40, coordY),
            ancho: 200,
            es_intermedia: true,
            atributos: [
              {
                id: -(baseTiempo * 100 + (contadorSecuencia++ % 100)),
                nombre: 'id',
                tipo: 'integer',
                es_clave: true,
                es_nulo: false,
                orden: 1
              }
            ]
          };

          entidadesNormalizadas.push(entIntermedia);
          entidadesMap.set(idIntermedio, entIntermedia);
          claseAsocIdReal = idIntermedio;
          intermediasEnlazadas.add(idIntermedio);
        }

        tipoRelacion = 'asociacion';
        cardOrigen = '0..*';
        cardDestino = '0..*';
      }

      const puertos = this.calcularPuertosRelacion(origIdReal, destIdReal, entidadesMap, conteoPares);

      relacionesNormalizadas.push({
        id: idRelTemporal,
        nombre_relacion: (rel.nombre_relacion || '').trim(),
        tipo: tipoRelacion,
        entidad_origen_id: origIdReal,
        entidad_destino_id: destIdReal,
        cardinalidad_origen: cardOrigen,
        cardinalidad_destino: cardDestino,
        clase_asociacion_id: claseAsocIdReal,
        puerto_origen: puertos.origen,
        puerto_destino: puertos.destino,
        vertices: [],
        destino_bloqueado: tipoRelacion === 'composicion'
      });
    }

    // 5. Garantizar que ninguna entidad intermedia quede aislada (sin relación)
    for (const entHuerfana of entidadesNormalizadas) {
      if (entHuerfana.es_intermedia && !intermediasEnlazadas.has(entHuerfana.id)) {
        let idA: number | null = null;
        let idB: number | null = null;

        // Probar si el nombre es compuesto ej. estudiante_materia
        const partes = entHuerfana.nombre.split('_');
        if (partes.length >= 2) {
          const nomA = partes[0].toLowerCase();
          const nomB = partes.slice(1).join('_').toLowerCase();
          idA = resolverEntidadId(nomA);
          idB = resolverEntidadId(nomB);
        }

        // Si no se dedujo por nombre, seleccionar las dos entidades más cercanas espacialmente
        if (idA === null || idB === null || idA === idB) {
          const otras = entidadesNormalizadas.filter(e => !e.es_intermedia && e.id !== entHuerfana.id);
          if (otras.length >= 2) {
            otras.sort((a, b) => {
              const distA = Math.hypot(a.coord_x - entHuerfana.coord_x, a.coord_y - entHuerfana.coord_y);
              const distB = Math.hypot(b.coord_x - entHuerfana.coord_x, b.coord_y - entHuerfana.coord_y);
              return distA - distB;
            });
            idA = otras[0].id;
            idB = otras[1].id;
          }
        }

        if (idA !== null && idB !== null && idA !== idB) {
          // Si ya existe una relación entre A y B sin clase de asociación, asignársela
          const relExistente = relacionesNormalizadas.find(
            r => ((r.entidad_origen_id === idA && r.entidad_destino_id === idB) ||
                  (r.entidad_origen_id === idB && r.entidad_destino_id === idA)) &&
                 !r.clase_asociacion_id
          );

          if (relExistente) {
            relExistente.clase_asociacion_id = entHuerfana.id;
            relExistente.tipo = 'asociacion';
            relExistente.cardinalidad_origen = '0..*';
            relExistente.cardinalidad_destino = '0..*';
            intermediasEnlazadas.add(entHuerfana.id);
          } else {
            // Crear la relación faltante entre A y B con la clase de asociación
            const idRelTemp = -(baseTiempo * 100 + (contadorSecuencia++ % 100));
            const puertos = this.calcularPuertosRelacion(idA, idB, entidadesMap, conteoPares);
            relacionesNormalizadas.push({
              id: idRelTemp,
              nombre_relacion: '',
              tipo: 'asociacion',
              entidad_origen_id: idA,
              entidad_destino_id: idB,
              cardinalidad_origen: '0..*',
              cardinalidad_destino: '0..*',
              clase_asociacion_id: entHuerfana.id,
              puerto_origen: puertos.origen,
              puerto_destino: puertos.destino,
              vertices: [],
              origen_bloqueado: false
            });
            intermediasEnlazadas.add(entHuerfana.id);
          }
        }
      }
    }

    return {
      entidades: entidadesNormalizadas,
      relaciones: relacionesNormalizadas
    };
  }

  private calcularPuertosRelacion(
    origId: number,
    destId: number,
    entidadesMap: Map<number, EntidadDiagrama>,
    conteoPares: Map<string, number>
  ): { origen: string; destino: string } {
    if (origId === destId) {
      const c = conteoPares.get(`${origId}_auto`) || 0;
      conteoPares.set(`${origId}_auto`, c + 1);
      const topIdx = [2, 1, 0][c % 3];
      const rightIdx = [0, 1, 2][c % 3];
      return { origen: `top-${topIdx}`, destino: `right-${rightIdx}` };
    }

    const clave = origId < destId ? `${origId}_${destId}` : `${destId}_${origId}`;
    const orden = conteoPares.get(clave) || 0;
    conteoPares.set(clave, orden + 1);

    const origEnt = entidadesMap.get(origId);
    const destEnt = entidadesMap.get(destId);

    const dx = (destEnt?.coord_x ?? 0) - (origEnt?.coord_x ?? 0);
    const dy = (destEnt?.coord_y ?? 0) - (origEnt?.coord_y ?? 0);

    const ordenOffset = [1, 2, 0, 3][orden % 4];
    const ordenOffsetVert = [1, 2, 0][orden % 3];

    if (Math.abs(dx) >= Math.abs(dy)) {
      if (dx >= 0) {
        return { origen: `right-${ordenOffset}`, destino: `left-${ordenOffset}` };
      }
      return { origen: `left-${ordenOffset}`, destino: `right-${ordenOffset}` };
    } else {
      if (dy >= 0) {
        return { origen: `bottom-${ordenOffsetVert}`, destino: `top-${ordenOffsetVert}` };
      }
      return { origen: `top-${ordenOffsetVert}`, destino: `bottom-${ordenOffsetVert}` };
    }
  }

  private normalizarAtributos(atributos: AtributoIARespuesta[]): AtributoDiagrama[] {
    const lista: AtributoDiagrama[] = [];
    const baseTiempo = Date.now() % 10000000;
    let ordenActual = 1;
    let tieneClave = false;

    for (const attr of atributos) {
      const nombreLimpio = (attr.nombre || `campo_${ordenActual}`).trim().replace(/^[-+~#]\s*/, '').replace(/\s+/g, '_').toLowerCase();
      const tipoLimpio = this.normalizarTipoAtributo(attr.tipo);
      const esClave = Boolean(attr.es_clave || nombreLimpio === 'id' || nombreLimpio === 'codigo');
      if (esClave) tieneClave = true;

      lista.push({
        id: -(baseTiempo * 100 + ordenActual),
        nombre: nombreLimpio,
        tipo: tipoLimpio,
        es_clave: esClave,
        es_nulo: Boolean(attr.es_nulo && !esClave),
        orden: ordenActual++
      });
    }

    // Si la entidad no tiene clave primaria identificada, se añade por defecto id: integer [pk]
    if (!tieneClave) {
      lista.unshift({
        id: -(baseTiempo * 100),
        nombre: 'id',
        tipo: 'integer',
        es_clave: true,
        es_nulo: false,
        orden: 1
      });
      // Reajustar orden
      lista.forEach((a, i) => (a.orden = i + 1));
    }

    return lista;
  }

  private normalizarTipoAtributo(tipoRaw?: string): AtributoDiagrama['tipo'] {
    if (!tipoRaw) return 'string';
    const t = tipoRaw.trim().toLowerCase();

    if (TIPOS_VALIDOS.includes(t as AtributoDiagrama['tipo'])) {
      return t as AtributoDiagrama['tipo'];
    }

    if (t.includes('int') || t.includes('serial') || t.includes('num')) return 'integer';
    if (t.includes('long') || t.includes('bigint')) return 'long';
    if (t.includes('float') || t.includes('double') || t.includes('decimal') || t.includes('real')) return 'double';
    if (t.includes('bool')) return 'boolean';
    if (t.includes('date') || t.includes('time') || t.includes('stamp')) return 'date';

    return 'string';
  }

  private normalizarTipoRelacion(tipoRaw?: string): RelacionDiagrama['tipo'] {
    if (!tipoRaw) return 'asociacion';
    const t = tipoRaw.trim().toLowerCase();
    if (TIPOS_RELACION_VALIDOS.includes(t as RelacionDiagrama['tipo'])) {
      return t as RelacionDiagrama['tipo'];
    }
    return 'asociacion';
  }

  private normalizarCardinalidad(cardRaw: string | undefined, defecto = ''): string {
    if (!cardRaw) return defecto;
    const c = cardRaw.trim();
    if (REGEX_CARDINALIDAD.test(c)) {
      return c;
    }
    return defecto;
  }

  /**
   * Extrae el contexto compacto del diagrama actual para enviarlo al modelo de IA.
   */
  public extraerContextoDiagrama(
    entidades: EntidadDiagrama[],
    relaciones: RelacionDiagrama[]
  ): ContextoDiagramaIA {
    return {
      entidades: entidades.map(e => ({
        id: e.id,
        nombre: e.nombre,
        estado: e.estado || 'activo',
        atributos: (e.atributos || []).map(a => ({
          nombre: a.nombre,
          tipo: a.tipo,
          es_clave: a.es_clave,
          es_nulo: Boolean(a.es_nulo)
        }))
      })),
      relaciones: relaciones.map(r => ({
        id: r.id,
        entidad_origen_id: r.entidad_origen_id,
        entidad_destino_id: r.entidad_destino_id,
        tipo: r.tipo,
        nombre_relacion: r.nombre_relacion
      }))
    };
  }

  /**
   * Calcula y asigna coordenadas espaciales al lote de entidades generadas por la IA,
   * evitando superposiciones y adaptándose al viewport visible.
   */
  public posicionarDiagramaGenerado(
    payload: DiagramaGeneradoPayload,
    centro: { x: number; y: number },
    cantExistente: number
  ): DiagramaGeneradoPayload {
    const offsetBase = (cantExistente % 8) * 40;
    const tienePosicionesIA = payload.entidades.some(
      e => e.pos_x !== undefined && e.pos_y !== undefined
    );
    const spanX = Math.max(900, payload.entidades.length * 180);
    const spanY = Math.max(650, payload.entidades.length * 90);

    for (let i = 0; i < payload.entidades.length; i++) {
      const ent = payload.entidades[i];

      if (tienePosicionesIA && ent.pos_x !== undefined && ent.pos_y !== undefined) {
        const relX = (ent.pos_x / 1000 - 0.5) * spanX;
        const relY = (ent.pos_y / 1000 - 0.5) * spanY;
        ent.coord_x = Math.max(40, Math.round(centro.x + relX - (ent.ancho || 200) / 2));
        ent.coord_y = Math.max(40, Math.round(centro.y + relY - 40));

        for (let j = 0; j < i; j++) {
          const prev = payload.entidades[j];
          if (Math.abs(ent.coord_x - prev.coord_x) < 210 && Math.abs(ent.coord_y - prev.coord_y) < 90) {
            ent.coord_x += 100;
            ent.coord_y += 80;
          }
        }
      } else {
        ent.coord_x = Math.round(centro.x - 100 + offsetBase + i * 60);
        ent.coord_y = Math.round(centro.y - 60 + offsetBase + i * 50);
      }
    }

    const entidadesMap = new Map<number, EntidadDiagrama>();
    for (const ent of payload.entidades) {
      entidadesMap.set(ent.id, ent);
    }

    // Posicionar estéticamente las tablas intermedias entre las dos entidades vinculadas
    for (const rel of payload.relaciones) {
      if (rel.clase_asociacion_id) {
        const entIntermedia = entidadesMap.get(rel.clase_asociacion_id);
        const entOrig = entidadesMap.get(rel.entidad_origen_id);
        const entDest = entidadesMap.get(rel.entidad_destino_id);

        if (entIntermedia && entOrig && entDest) {
          const distOrig = Math.hypot(entIntermedia.coord_x - entOrig.coord_x, entIntermedia.coord_y - entOrig.coord_y);
          const distDest = Math.hypot(entIntermedia.coord_x - entDest.coord_x, entIntermedia.coord_y - entDest.coord_y);
          if (!tienePosicionesIA || distOrig < 100 || distDest < 100) {
            entIntermedia.coord_x = Math.round((entOrig.coord_x + entDest.coord_x) / 2);
            entIntermedia.coord_y = Math.round(Math.min(entOrig.coord_y, entDest.coord_y) - 110);
            if (entIntermedia.coord_y < 40) {
              entIntermedia.coord_y = Math.round((entOrig.coord_y + entDest.coord_y) / 2 + 130);
            }
          }
        }
      }
    }

    // Recalcular puertos óptimos para todas las relaciones con base en las coordenadas finales
    const conteoPares = new Map<string, number>();
    for (const rel of payload.relaciones) {
      const puertos = this.calcularPuertosRelacion(
        rel.entidad_origen_id,
        rel.entidad_destino_id,
        entidadesMap,
        conteoPares
      );
      rel.puerto_origen = puertos.origen;
      rel.puerto_destino = puertos.destino;
    }

    return payload;
  }

  /**
   * Procesa las instrucciones delta generadas por la IA, transformando comandos abstractos
   * en objetos de dominio listos para ser renderizados y sincronizados.
   */
  public procesarDelta(
    delta: DeltaInstruccionIARespuesta,
    getEntidadFn: (id: number) => EntidadDiagrama | undefined,
    centro: { x: number; y: number },
    cantExistente: number,
    generarIdFn: () => number,
    entidadesExistentes: EntidadDiagrama[] = []
  ): ResultadoProcesarDelta {
    const entidadesACrear: EntidadDiagrama[] = [];
    const entidadesAModificar: EntidadDiagrama[] = [];
    const relacionesACrear: RelacionDiagrama[] = [];

    // Mapa para localizar entidades creadas en este mismo lote por nombre
    const entidadesCreadasPorNombre = new Map<string, EntidadDiagrama>();

    // Mapas de búsqueda rápida para entidades existentes
    const mapaExistentesPorId = new Map<number, EntidadDiagrama>();
    const mapaExistentesPorNombre = new Map<string, EntidadDiagrama>();
    for (const ent of entidadesExistentes) {
      mapaExistentesPorId.set(Number(ent.id), ent);
      if (ent.nombre) {
        mapaExistentesPorNombre.set(ent.nombre.trim().toLowerCase(), ent);
      }
    }

    // 1. Entidades a crear
    if (delta.entidades_a_crear?.length) {
      const offsetBase = (cantExistente % 6) * 35;
      for (let i = 0; i < delta.entidades_a_crear.length; i++) {
        const entIA = delta.entidades_a_crear[i];
        const idTemp = generarIdFn();
        let ordenAttr = 1;
        let tieneClave = false;

        const atributos: AtributoDiagrama[] = (entIA.atributos || []).map(a => {
          const nombreLimpio = (a.nombre || 'campo').trim().replace(/^[-+~#]\s*/, '').replace(/\s+/g, '_').toLowerCase();
          const tipoLimpio = this.normalizarTipoAtributo(a.tipo);
          const esClave = Boolean(a.es_clave || nombreLimpio === 'id' || nombreLimpio === 'codigo');
          if (esClave) tieneClave = true;
          return {
            id: generarIdFn(),
            nombre: nombreLimpio,
            tipo: tipoLimpio,
            es_clave: esClave,
            es_nulo: Boolean(a.es_nulo && !esClave),
            orden: ordenAttr++
          };
        });

        // Garantizar clave primaria si no la traía
        if (!tieneClave) {
          atributos.unshift({
            id: generarIdFn(),
            nombre: 'id',
            tipo: 'integer',
            es_clave: true,
            es_nulo: false,
            orden: 1
          });
          atributos.forEach((a, idx) => (a.orden = idx + 1));
        }

        const nombreLimpio = (entIA.nombre || 'Entidad').trim().replace(/\s+/g, '_');
        const entidadNueva: EntidadDiagrama = {
          id: idTemp,
          nombre: nombreLimpio,
          estado: 'activo',
          coord_x: Math.round(centro.x - 80 + offsetBase + i * 50),
          coord_y: Math.round(centro.y - 50 + offsetBase + i * 40),
          ancho: 200,
          es_intermedia: Boolean(entIA.es_intermedia),
          atributos
        };

        entidadesACrear.push(entidadNueva);
        entidadesCreadasPorNombre.set(nombreLimpio.toLowerCase(), entidadNueva);
      }
    }

    // 2. Entidades a modificar (con validación de estado bloqueado)
    if (delta.entidades_a_modificar?.length) {
      for (const mod of delta.entidades_a_modificar) {
        // Resolver la entidad existente por ID numérico o por nombre
        let entidadExistente: EntidadDiagrama | undefined;
        if (mod.entidad_id !== undefined && mod.entidad_id !== null && !isNaN(Number(mod.entidad_id))) {
          const numId = Number(mod.entidad_id);
          entidadExistente = getEntidadFn(numId) || mapaExistentesPorId.get(numId);
        }
        if (!entidadExistente && mod.entidad_nombre && mod.entidad_nombre.trim()) {
          const nom = mod.entidad_nombre.trim().toLowerCase();
          entidadExistente = mapaExistentesPorNombre.get(nom) ||
            entidadesExistentes.find(e => (e.nombre || '').trim().toLowerCase() === nom);
        }
        if (!entidadExistente && typeof mod.entidad_id === 'string' && isNaN(Number(mod.entidad_id))) {
          const nom = (mod.entidad_id as string).trim().toLowerCase();
          entidadExistente = mapaExistentesPorNombre.get(nom) ||
            entidadesExistentes.find(e => (e.nombre || '').trim().toLowerCase() === nom);
        }

        if (!entidadExistente) continue;

        // Control de Exclusión Mutua: Si la entidad está bloqueada, no puede modificarse
        if (entidadExistente.estado === 'bloqueado') {
          continue;
        }

        let nombreActualizado = entidadExistente.nombre;
        if (mod.nuevo_nombre && mod.nuevo_nombre.trim()) {
          nombreActualizado = mod.nuevo_nombre.trim().replace(/\s+/g, '_');
        }

        let attrsActuales = entidadExistente.atributos ? [...entidadExistente.atributos] : [];

        // 2.A Modificar atributos existentes (cambio de tipo, clave, nulabilidad o renombrado)
        for (const attrMod of mod.atributos_a_modificar || []) {
          const nombreBuscado = (attrMod.nombre_original || attrMod.nombre || '').trim().toLowerCase();
          const idx = attrsActuales.findIndex(a => a.nombre.toLowerCase() === nombreBuscado);
          if (idx !== -1) {
            const attrExistente = attrsActuales[idx];
            const nuevoNombre = attrMod.nombre ? attrMod.nombre.trim().replace(/^[-+~#]\s*/, '').replace(/\s+/g, '_').toLowerCase() : attrExistente.nombre;
            const nuevoTipo = attrMod.tipo ? this.normalizarTipoAtributo(attrMod.tipo) : attrExistente.tipo;
            const nuevoEsClave = attrMod.es_clave !== undefined ? Boolean(attrMod.es_clave) : attrExistente.es_clave;
            const nuevoEsNulo = attrMod.es_nulo !== undefined ? Boolean(attrMod.es_nulo && !nuevoEsClave) : attrExistente.es_nulo;

            attrsActuales[idx] = {
              ...attrExistente,
              nombre: nuevoNombre || attrExistente.nombre,
              tipo: nuevoTipo,
              es_clave: nuevoEsClave,
              es_nulo: nuevoEsNulo
            };
          }
        }

        // 2.B Eliminar atributos específicos de la entidad
        if (mod.atributos_a_eliminar && mod.atributos_a_eliminar.length > 0) {
          const aEliminar = new Set(mod.atributos_a_eliminar.map(n => n.trim().toLowerCase()));
          attrsActuales = attrsActuales.filter(a => !aEliminar.has(a.nombre.toLowerCase()));
          attrsActuales.forEach((a, index) => (a.orden = index + 1));
        }

        // 2.C Agregar nuevos atributos (con prevención de duplicados si ya existe)
        let maxOrden = attrsActuales.reduce((max, a) => Math.max(max, a.orden), 0);
        for (const attrNuevo of mod.atributos_nuevos || []) {
          const nombreLimpio = (attrNuevo.nombre || 'campo').trim().replace(/^[-+~#]\s*/, '').replace(/\s+/g, '_').toLowerCase();
          const tipoLimpio = this.normalizarTipoAtributo(attrNuevo.tipo);
          const esClave = Boolean(attrNuevo.es_clave);

          const idxExistente = attrsActuales.findIndex(a => a.nombre.toLowerCase() === nombreLimpio);
          if (idxExistente !== -1) {
            // Ya existía un atributo con ese nombre -> MODIFICARLO en lugar de duplicarlo
            const nuevoTipo = attrNuevo.tipo ? tipoLimpio : attrsActuales[idxExistente].tipo;
            const nuevoEsClave = attrNuevo.es_clave !== undefined ? esClave : attrsActuales[idxExistente].es_clave;
            const nuevoEsNulo = attrNuevo.es_nulo !== undefined ? Boolean(attrNuevo.es_nulo && !nuevoEsClave) : attrsActuales[idxExistente].es_nulo;
            attrsActuales[idxExistente] = {
              ...attrsActuales[idxExistente],
              tipo: nuevoTipo,
              es_clave: nuevoEsClave,
              es_nulo: nuevoEsNulo
            };
          } else {
            // Es genuinamente nuevo -> crearlo
            maxOrden++;
            attrsActuales.push({
              id: generarIdFn(),
              nombre: nombreLimpio,
              tipo: tipoLimpio,
              es_clave: esClave,
              es_nulo: Boolean(attrNuevo.es_nulo && !esClave),
              orden: maxOrden
            });
          }
        }

        entidadesAModificar.push({
          ...entidadExistente,
          nombre: nombreActualizado,
          atributos: attrsActuales
        });
      }
    }

    // Función auxiliar para resolver entidades por ID o por nombre (soporta nuevas y existentes)
    const resolverEntidad = (
      idRef?: number | string | null,
      nombreRef?: string | null
    ): EntidadDiagrama | undefined => {
      // 1. Buscar por nombre en las entidades recién creadas en este delta
      if (nombreRef && nombreRef.trim()) {
        const nomLimpio = nombreRef.trim().toLowerCase();
        const creada = entidadesCreadasPorNombre.get(nomLimpio) ||
          entidadesACrear.find(e => e.nombre.toLowerCase() === nomLimpio);
        if (creada) return creada;
      }

      // 2. Buscar por ID numérico en las entidades recién creadas
      if (idRef !== undefined && idRef !== null && !isNaN(Number(idRef))) {
        const numId = Number(idRef);
        const creadaPorId = entidadesACrear.find(e => e.id === numId);
        if (creadaPorId) return creadaPorId;
      }

      // 3. Buscar por ID numérico en las entidades existentes del diagrama
      if (idRef !== undefined && idRef !== null && !isNaN(Number(idRef))) {
        const numId = Number(idRef);
        const existentePorId = getEntidadFn(numId) || mapaExistentesPorId.get(numId);
        if (existentePorId) return existentePorId;
      }

      // 4. Buscar por nombre en las entidades existentes del diagrama
      if (nombreRef && nombreRef.trim()) {
        const nomLimpio = nombreRef.trim().toLowerCase();
        const existentePorNombre = mapaExistentesPorNombre.get(nomLimpio) ||
          entidadesExistentes.find(e => (e.nombre || '').trim().toLowerCase() === nomLimpio);
        if (existentePorNombre) return existentePorNombre;
      }

      // 5. Fallback por si el LLM envió el nombre de la entidad dentro de idRef como string
      if (typeof idRef === 'string' && isNaN(Number(idRef)) && idRef.trim()) {
        const nomId = idRef.trim().toLowerCase();
        return entidadesCreadasPorNombre.get(nomId) ||
          entidadesACrear.find(e => e.nombre.toLowerCase() === nomId) ||
          mapaExistentesPorNombre.get(nomId) ||
          entidadesExistentes.find(e => (e.nombre || '').trim().toLowerCase() === nomId);
      }

      return undefined;
    };

    // 3. Relaciones a crear
    if (delta.relaciones_a_crear?.length) {
      for (const relIA of delta.relaciones_a_crear) {
        const entidadOrigen = resolverEntidad(relIA.entidad_origen_id, relIA.entidad_origen_nombre);
        const entidadDestino = resolverEntidad(relIA.entidad_destino_id, relIA.entidad_destino_nombre);

        if (!entidadOrigen || !entidadDestino) {
          // Si no se puede resolver uno de los extremos, omitir para no corromper el canvas
          continue;
        }

        // Posicionamiento inteligente cuando una entidad nueva se relaciona con otra
        const origenEsNuevo = entidadesACrear.some(e => e.id === entidadOrigen.id);
        const destinoEsNuevo = entidadesACrear.some(e => e.id === entidadDestino.id);

        if (!origenEsNuevo && destinoEsNuevo) {
          // Destino es nueva: ubicarla adyacente a la derecha de origen
          entidadDestino.coord_x = entidadOrigen.coord_x + 280;
          entidadDestino.coord_y = entidadOrigen.coord_y;
        } else if (origenEsNuevo && !destinoEsNuevo) {
          // Origen es nueva: ubicarla adyacente a la izquierda de destino
          entidadOrigen.coord_x = Math.max(40, entidadDestino.coord_x - 280);
          entidadOrigen.coord_y = entidadDestino.coord_y;
        } else if (origenEsNuevo && destinoEsNuevo && entidadesACrear.length === 2 && !entidadOrigen.es_intermedia && !entidadDestino.es_intermedia) {
          // Ambas son nuevas: distribuirlas lado a lado armónicamente
          entidadDestino.coord_x = entidadOrigen.coord_x + 280;
          entidadDestino.coord_y = entidadOrigen.coord_y;
        }

        const cardOrig = (relIA.cardinalidad_origen || '').trim();
        const cardDest = (relIA.cardinalidad_destino || '').trim();

        const esMuchosAMuchos = Boolean(
          relIA.clase_asociacion_nombre ||
          relIA.tipo === 'clase_asociacion' ||
          ((cardOrig === '0..*' || cardOrig === '*' || cardOrig === '1..*') &&
           (cardDest === '0..*' || cardDest === '*' || cardDest === '1..*'))
        );

        let claseAsociacionId: number | null = relIA.clase_asociacion_id ?? null;

        if (esMuchosAMuchos) {
          // Intentar resolver la entidad intermedia existente en este lote
          let entIntermedia: EntidadDiagrama | undefined;

          if (relIA.clase_asociacion_nombre) {
            const nomBuscado = relIA.clase_asociacion_nombre.trim().toLowerCase();
            entIntermedia = entidadesCreadasPorNombre.get(nomBuscado) ||
              entidadesACrear.find(e => e.nombre.toLowerCase() === nomBuscado);
          }

          if (!entIntermedia) {
            // Buscar si hay alguna entidad intermedia creada en este lote que no esté enlazada aún
            entIntermedia = entidadesACrear.find(e => e.es_intermedia && !relacionesACrear.some(r => r.clase_asociacion_id === e.id));
          }

          // Fallback defensivo: si no vino la entidad intermedia, la creamos automáticamente
          if (!entIntermedia) {
            const nomOrig = (entidadOrigen?.nombre || 'origen').toLowerCase().trim().replace(/\s+/g, '_');
            const nomDest = (entidadDestino?.nombre || 'destino').toLowerCase().trim().replace(/\s+/g, '_');
            const nombreIntermedio = relIA.clase_asociacion_nombre?.trim().replace(/\s+/g, '_').toLowerCase() || `${nomOrig}_${nomDest}`;

            const idIntermedio = generarIdFn();
            entIntermedia = {
              id: idIntermedio,
              nombre: nombreIntermedio,
              estado: 'activo',
              coord_x: Math.round(centro.x),
              coord_y: Math.round(centro.y - 80),
              ancho: 200,
              es_intermedia: true,
              atributos: [
                {
                  id: generarIdFn(),
                  nombre: 'id',
                  tipo: 'integer',
                  es_clave: true,
                  es_nulo: false,
                  orden: 1
                }
              ]
            };
            entidadesACrear.push(entIntermedia);
            entidadesCreadasPorNombre.set(nombreIntermedio, entIntermedia);
          } else {
            entIntermedia.es_intermedia = true;
          }

          // Ubicar estéticamente la entidad intermedia entre el origen y el destino
          entIntermedia.coord_x = Math.round((entidadOrigen.coord_x + entidadDestino.coord_x) / 2);
          entIntermedia.coord_y = Math.round(Math.min(entidadOrigen.coord_y, entidadDestino.coord_y) - 100);
          if (entIntermedia.coord_y < 40) {
            entIntermedia.coord_y = Math.round((entidadOrigen.coord_y + entidadDestino.coord_y) / 2 + 120);
          }

          claseAsociacionId = entIntermedia.id;
        }

        const tipoFinal = esMuchosAMuchos ? 'asociacion' : this.normalizarTipoRelacion(relIA.tipo);
        const cardOrigFinal = esMuchosAMuchos ? '0..*' : this.normalizarCardinalidad(relIA.cardinalidad_origen, '');
        const cardDestFinal = esMuchosAMuchos ? '0..*' : this.normalizarCardinalidad(relIA.cardinalidad_destino, '');

        // Calcular puertos óptimos según la posición relativa de las cajas
        let puertoOrigen = 'right-1';
        let puertoDestino = 'left-1';
        const mapaTemp = new Map<number, EntidadDiagrama>();
        mapaTemp.set(entidadOrigen.id, entidadOrigen);
        mapaTemp.set(entidadDestino.id, entidadDestino);
        const puertos = this.calcularPuertosRelacion(entidadOrigen.id, entidadDestino.id, mapaTemp, new Map());
        puertoOrigen = puertos.origen;
        puertoDestino = puertos.destino;

        relacionesACrear.push({
          id: generarIdFn(),
          nombre_relacion: relIA.nombre_relacion || '',
          tipo: tipoFinal,
          entidad_origen_id: entidadOrigen.id,
          entidad_destino_id: entidadDestino.id,
          cardinalidad_origen: cardOrigFinal,
          cardinalidad_destino: cardDestFinal,
          clase_asociacion_id: claseAsociacionId,
          puerto_origen: puertoOrigen,
          puerto_destino: puertoDestino,
          vertices: [],
          destino_bloqueado: tipoFinal === 'composicion'
        });
      }
    }

    // Filtrar entidades a eliminar para proteger entidades bloqueadas
    const entidadesAEliminar: number[] = (delta.entidades_a_eliminar || []).filter(id => {
      const entidad = getEntidadFn(id) || mapaExistentesPorId.get(Number(id));
      return !entidad || entidad.estado !== 'bloqueado';
    });

    return {
      entidadesACrear,
      entidadesAModificar,
      entidadesAEliminar,
      relacionesACrear,
      relacionesAEliminar: delta.relaciones_a_eliminar || []
    };
  }
}

export interface ResultadoProcesarDelta {
  entidadesACrear: EntidadDiagrama[];
  entidadesAModificar: EntidadDiagrama[];
  entidadesAEliminar: number[];
  relacionesACrear: RelacionDiagrama[];
  relacionesAEliminar: number[];
}
