import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { DiagramaCargaInicial, ProyectoDiagrama, RelacionDiagrama } from '../interfaces/diagrama.interface';
import { UsuarioBusqueda, ColaboradorProyecto, RespuestaAccionColaborador } from '../interfaces/colaborador.interface';

@Injectable({
  providedIn: 'root'
})
export class WhiteboardApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/modelado`;
  private readonly usuarioUrl = `${environment.apiUrl}/usuario`;

  public getDiagrama(proyectoId: number): Observable<DiagramaCargaInicial> {
    return this.http.get<DiagramaCargaInicial>(
      `${this.baseUrl}/proyectos/${proyectoId}/diagrama/`
    ).pipe(
      map(datos => this.reconciliarDatosDiagrama(datos))
    );
  }

  /**
   * Reconcilia la respuesta relacional de la BD con el snapshot visual guardado
   * (vértices, puertos, multiplicidades personalizadas, etiquetas de relación).
   */
  private reconciliarDatosDiagrama(datos: DiagramaCargaInicial): DiagramaCargaInicial {
    const snapshotRelaciones = (datos.proyecto?.datos_diagrama as Record<string, unknown>)?.['relaciones'] as RelacionDiagrama[] | undefined;
    const snapshotMap = new Map<number, RelacionDiagrama>();
    if (snapshotRelaciones && Array.isArray(snapshotRelaciones)) {
      snapshotRelaciones.forEach(r => snapshotMap.set(r.id, r));
    }

    const relacionesFinales: RelacionDiagrama[] = [];
    const idsAgregados = new Set<number>();

    (datos.relaciones || []).forEach(r => {
      const deSnapshot = snapshotMap.get(r.id);
      const tipo = r.tipo;
      idsAgregados.add(r.id);
      let cardOrig = (r.cardinalidad_origen !== undefined && r.cardinalidad_origen !== null)
        ? r.cardinalidad_origen
        : (deSnapshot?.cardinalidad_origen ?? '');
      let cardDest = (r.cardinalidad_destino !== undefined && r.cardinalidad_destino !== null)
        ? r.cardinalidad_destino
        : (deSnapshot?.cardinalidad_destino ?? '');
      if (cardOrig === '*') cardOrig = '0..*';
      if (cardDest === '*') cardDest = '0..*';

      relacionesFinales.push({
        ...r,
        nombre_relacion: r.nombre_relacion || deSnapshot?.nombre_relacion || '',
        clase_asociacion_id: r.clase_asociacion_id ?? deSnapshot?.clase_asociacion_id ?? null,
        puerto_origen: r.puerto_origen || deSnapshot?.puerto_origen,
        puerto_destino: r.puerto_destino || deSnapshot?.puerto_destino,
        vertices: r.vertices ?? deSnapshot?.vertices ?? [],
        cardinalidad_origen: cardOrig,
        cardinalidad_destino: cardDest,
        origen_bloqueado: r.origen_bloqueado ?? deSnapshot?.origen_bloqueado ?? false,
        destino_bloqueado: r.destino_bloqueado ?? deSnapshot?.destino_bloqueado ?? (tipo === 'composicion')
      });
    });

    if (snapshotRelaciones && Array.isArray(snapshotRelaciones)) {
      snapshotRelaciones.forEach(r => {
        if (r && r.id && !idsAgregados.has(r.id)) {
          idsAgregados.add(r.id);
          relacionesFinales.push(r);
        }
      });
    }

    // Salvaguarda: si existen entidades intermedias sin clase_asociacion_id vinculada, resolver
    const intermediasHuerfanas = (datos.entidades || []).filter(
      e => e.es_intermedia && !relacionesFinales.some(r => r.clase_asociacion_id === e.id)
    );

    if (intermediasHuerfanas.length > 0) {
      intermediasHuerfanas.forEach(entIntermedia => {
        const relCandidata = relacionesFinales.find(
          r => r.tipo === 'asociacion' && !r.clase_asociacion_id &&
               r.entidad_origen_id !== entIntermedia.id &&
               r.entidad_destino_id !== entIntermedia.id
        );
        if (relCandidata) {
          relCandidata.clase_asociacion_id = entIntermedia.id;
        }
      });
    }

    return {
      ...datos,
      relaciones: relacionesFinales
    };
  }

  public renombrarProyecto(proyectoId: number, nombre: string): Observable<ProyectoDiagrama> {
    return this.http.patch<ProyectoDiagrama>(
      `${this.baseUrl}/proyectos/${proyectoId}/`,
      { nombre }
    );
  }

  public buscarUsuarios(termino: string): Observable<UsuarioBusqueda[]> {
    return this.http.get<UsuarioBusqueda[]>(
      `${this.usuarioUrl}/buscar/`,
      { params: { q: termino } }
    );
  }

  public obtenerColaboradores(proyectoId: number): Observable<ColaboradorProyecto[]> {
    return this.http.get<ColaboradorProyecto[]>(
      `${this.baseUrl}/proyectos/${proyectoId}/colaboradores/`
    );
  }

  public invitarColaborador(
    proyectoId: number,
    datos: { email?: string; username?: string }
  ): Observable<RespuestaAccionColaborador> {
    return this.http.post<RespuestaAccionColaborador>(
      `${this.baseUrl}/proyectos/${proyectoId}/invitar/`,
      datos
    );
  }

  public reenviarInvitacion(
    proyectoId: number,
    colaboradorId: number
  ): Observable<RespuestaAccionColaborador> {
    return this.http.post<RespuestaAccionColaborador>(
      `${this.baseUrl}/proyectos/${proyectoId}/colaboradores/${colaboradorId}/reenviar/`,
      {}
    );
  }

  public eliminarColaborador(
    proyectoId: number,
    colaboradorId: number
  ): Observable<RespuestaAccionColaborador> {
    return this.http.delete<RespuestaAccionColaborador>(
      `${this.baseUrl}/proyectos/${proyectoId}/colaboradores/${colaboradorId}/`
    );
  }
}
