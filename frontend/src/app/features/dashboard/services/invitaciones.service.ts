import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, Subject, map, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  InvitacionPendiente,
  RespuestaAceptarInvitacion,
  RespuestaRechazarInvitacion
} from '../interfaces/invitacion.interface';

@Injectable({
  providedIn: 'root'
})
export class InvitacionesService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/modelado/invitaciones`;

  private readonly invitacionesSubject = new BehaviorSubject<InvitacionPendiente[]>([]);
  public readonly invitaciones$: Observable<InvitacionPendiente[]> = this.invitacionesSubject.asObservable();
  public readonly conteoPendientes$: Observable<number> = this.invitaciones$.pipe(
    map((invs: InvitacionPendiente[]) => invs.length)
  );

  /** Emite cada vez que una invitación es aceptada para sincronizar componentes (ej. lista de proyectos) */
  public readonly invitacionAceptada$ = new Subject<void>();

  public cargarInvitaciones(): Observable<InvitacionPendiente[]> {
    return this.http.get<InvitacionPendiente[]>(`${this.baseUrl}/`).pipe(
      tap((invitaciones: InvitacionPendiente[]) => {
        this.invitacionesSubject.next(invitaciones);
      })
    );
  }

  public aceptarInvitacion(id: number): Observable<RespuestaAceptarInvitacion> {
    return this.http.post<RespuestaAceptarInvitacion>(`${this.baseUrl}/${id}/aceptar/`, {}).pipe(
      tap(() => {
        const actuales = this.invitacionesSubject.value;
        this.invitacionesSubject.next(actuales.filter((inv: InvitacionPendiente) => inv.id !== id));
        this.invitacionAceptada$.next();
      })
    );
  }

  public rechazarInvitacion(id: number): Observable<RespuestaRechazarInvitacion> {
    return this.http.post<RespuestaRechazarInvitacion>(`${this.baseUrl}/${id}/rechazar/`, {}).pipe(
      tap(() => {
        const actuales = this.invitacionesSubject.value;
        this.invitacionesSubject.next(actuales.filter((inv: InvitacionPendiente) => inv.id !== id));
      })
    );
  }
}
