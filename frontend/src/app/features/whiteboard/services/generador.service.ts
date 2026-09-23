import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { RespuestaImportacionXML } from '../interfaces/generador.interface';

@Injectable({
  providedIn: 'root'
})
export class GeneradorService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/generador`;

  /**
   * Solicita al backend la generación del archivo XML 2.1 estándar (OMG UML / XMI 2.1).
   */
  public exportarDiagramaXML(proyectoId: number): Observable<Blob> {
    return this.http.get(
      `${this.baseUrl}/proyectos/${proyectoId}/exportar-xml/`,
      { responseType: 'blob' }
    );
  }

  /**
   * Descarga directamente en el navegador del usuario el archivo XML exportado.
   */
  public descargarArchivoXML(proyectoId: number, nombreSugerido?: string): void {
    this.exportarDiagramaXML(proyectoId).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = nombreSugerido ? `${nombreSugerido}_diagrama_ea.xml` : `proyecto_${proyectoId}_diagrama_ea.xml`;
        document.body.appendChild(enlace);
        enlace.click();
        document.body.removeChild(enlace);
        window.URL.revokeObjectURL(url);
      },
      error: (error: unknown) => {
        console.error('[GENERADOR_SERVICE] Error descargando archivo XML 2.1:', error);
      }
    });
  }

  /**
   * Carga un archivo XML 2.1 para importarlo e incorporarlo a la base de datos del proyecto.
   */
  public importarDiagramaXML(
    proyectoId: number,
    archivo: File,
    reemplazarExistente: boolean = true
  ): Observable<RespuestaImportacionXML> {
    const formData = new FormData();
    formData.append('archivo_xml', archivo);
    formData.append('reemplazar_existente', String(reemplazarExistente));

    return this.http.post<RespuestaImportacionXML>(
      `${this.baseUrl}/proyectos/${proyectoId}/importar-xml/`,
      formData
    );
  }
}
