import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Proyecto, ProyectoCreateRequest } from '../interfaces/proyecto.interface';

@Injectable({
  providedIn: 'root'
})
export class ProjectsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/modelado/proyectos`;

  public getProyectos(): Observable<Proyecto[]> {
    return this.http.get<Proyecto[]>(`${this.baseUrl}/`);
  }

  public getProyecto(id: number): Observable<Proyecto> {
    return this.http.get<Proyecto>(`${this.baseUrl}/${id}/`);
  }

  public crearProyecto(data: ProyectoCreateRequest): Observable<Proyecto> {
    return this.http.post<Proyecto>(`${this.baseUrl}/`, data);
  }
}
