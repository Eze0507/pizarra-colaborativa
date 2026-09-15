import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { DiagramaCargaInicial, ProyectoDiagrama } from '../interfaces/diagrama.interface';
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
    );
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
