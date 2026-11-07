import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  DescargaSpringPreparada,
  ErrorGeneracionSpring,
  RespuestaImportacionXML,
  SolicitudGeneracionSpring
} from '../interfaces/generador.interface';

const MAX_ERROR_BLOB_BYTES = 256 * 1024;
const ZIP_CONTENT_TYPES = new Set(['application/zip', 'application/x-zip-compressed']);

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
    expectedRevision: number,
    reemplazarExistente: boolean = true
  ): Observable<RespuestaImportacionXML> {
    const formData = new FormData();
    formData.append('archivo_xml', archivo);
    formData.append('reemplazar_existente', String(reemplazarExistente));
    formData.append('expected_revision', String(expectedRevision));

    return this.http.post<RespuestaImportacionXML>(
      `${this.baseUrl}/proyectos/${proyectoId}/importar-xml/`,
      formData
    );
  }

  public generarSpringBoot(
    proyectoId: number,
    solicitud: SolicitudGeneracionSpring
  ): Observable<HttpResponse<Blob>> {
    return this.http.post(
      `${this.baseUrl}/proyectos/${proyectoId}/spring-boot/`,
      solicitud,
      { responseType: 'blob', observe: 'response' }
    );
  }

  public async prepararDescargaSpring(
    response: HttpResponse<Blob>,
    fallbackName: string
  ): Promise<DescargaSpringPreparada> {
    const blob = response.body;
    if (!blob || blob.size === 0) {
      throw new Error('El servidor devolvió un archivo vacío.');
    }
    const rawType = response.headers.get('Content-Type') || blob.type || '';
    const contentType = rawType.split(';', 1)[0].trim().toLowerCase();
    if (!ZIP_CONTENT_TYPES.has(contentType)) {
      throw new Error('La respuesta recibida no es un archivo ZIP válido.');
    }
    const signature = new Uint8Array(await blob.slice(0, 4).arrayBuffer());
    const validSignature = signature.length === 4 && signature[0] === 0x50 && signature[1] === 0x4b && (
      (signature[2] === 0x03 && signature[3] === 0x04) ||
      (signature[2] === 0x05 && signature[3] === 0x06) ||
      (signature[2] === 0x07 && signature[3] === 0x08)
    );
    if (!validSignature) {
      throw new Error('La respuesta no contiene una firma ZIP reconocida.');
    }
    return {
      blob,
      filename: this.nombreDescargaSeguro(
        response.headers.get('Content-Disposition'), fallbackName
      )
    };
  }

  public iniciarDescarga(preparada: DescargaSpringPreparada): void {
    const objectUrl = window.URL.createObjectURL(preparada.blob);
    const anchor = document.createElement('a');
    anchor.href = objectUrl;
    anchor.download = preparada.filename;
    anchor.style.display = 'none';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 0);
  }

  public async leerErrorGeneracion(error: HttpErrorResponse): Promise<ErrorGeneracionSpring> {
    const fallback = this.mensajePorEstado(error.status);
    if (!(error.error instanceof Blob) || error.error.size === 0 || error.error.size > MAX_ERROR_BLOB_BYTES) {
      return { code: `http_${error.status || 0}`, message: fallback, status: error.status };
    }
    try {
      const parsed = JSON.parse(await error.error.text()) as Record<string, unknown>;
      return {
        code: typeof parsed['code'] === 'string' ? parsed['code'] : `http_${error.status || 0}`,
        message: typeof parsed['message'] === 'string'
          ? parsed['message']
          : typeof parsed['detail'] === 'string' ? parsed['detail'] : fallback,
        details: parsed['details'],
        status: error.status,
        current_revision: typeof parsed['current_revision'] === 'number'
          ? parsed['current_revision'] : undefined
      };
    } catch {
      return { code: `http_${error.status || 0}`, message: fallback, status: error.status };
    }
  }

  public describirErrorGeneracion(error: ErrorGeneracionSpring): string {
    const parts = [`${error.code}: ${error.message}`];
    const details = this.asRecord(error.details);
    if (typeof details?.['perfil'] === 'string') parts.push(`Perfil: ${details['perfil']}.`);
    const diagnostics = Array.isArray(details?.['diagnosticos'])
      ? details?.['diagnosticos'] as unknown[]
      : Array.isArray(details?.['hallazgos']) ? details?.['hallazgos'] as unknown[] : [];
    const first = this.asRecord(diagnostics[0]);
    if (first) {
      const code = typeof first['codigo'] === 'string' ? first['codigo'] : '';
      const message = typeof first['mensaje'] === 'string' ? first['mensaje'] : '';
      if (code || message) parts.push(`${code}${code && message ? ': ' : ''}${message}`);
      const target = this.asRecord(first['objetivo']);
      if (target && (target['tipo'] || target['id'] !== undefined)) {
        parts.push(`Elemento: ${String(target['tipo'] || 'modelo')} ${String(target['id'] ?? '')}.`);
      }
    }
    parts.push(this.sugerenciaError(error.code));
    return parts.join(' ').slice(0, 900);
  }

  private nombreDescargaSeguro(contentDisposition: string | null, fallbackName: string): string {
    let candidate = '';
    if (contentDisposition) {
      const encoded = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(contentDisposition)?.[1];
      if (encoded) {
        try { candidate = decodeURIComponent(encoded.trim().replace(/^"|"$/g, '')); } catch { candidate = ''; }
      }
      if (!candidate) {
        candidate = /filename\s*=\s*"([^"]+)"/i.exec(contentDisposition)?.[1]
          || /filename\s*=\s*([^;]+)/i.exec(contentDisposition)?.[1]?.trim()
          || '';
      }
    }
    candidate = candidate.split(/[\\/]/).pop() || '';
    candidate = candidate.replace(/[\u0000-\u001f\u007f<>:"|?*]/g, '').replace(/\.\.+/g, '.').trim();
    const reserved = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(candidate);
    if (!candidate || candidate.startsWith('.') || candidate.length > 128 || reserved) {
      candidate = fallbackName.replace(/[^a-zA-Z0-9_-]/g, '-').slice(0, 100) || 'proyecto-spring';
    }
    if (!candidate.toLowerCase().endsWith('.zip')) candidate += '.zip';
    return candidate;
  }

  private mensajePorEstado(status: number): string {
    switch (status) {
      case 400: return 'La configuración de generación no es válida.';
      case 401: return 'La sesión no está autenticada.';
      case 403: return 'No tienes permiso para generar este proyecto.';
      case 409: return 'La revisión del diagrama está desactualizada.';
      case 422: return 'El modelo UML no es compatible con la generación solicitada.';
      default: return 'No se pudo generar el proyecto Spring Boot.';
    }
  }

  private sugerenciaError(code: string): string {
    if (code === 'stale_revision') return 'Recupere o reconcilie la revisión antes de volver a generar.';
    if (code === 'CRUD_UNSUPPORTED_RELATION_PAYLOAD') {
      return 'Genere solo modelo y repositorios o revise conscientemente las relaciones antes de solicitar CRUD.';
    }
    if (code.includes('LIMIT')) return 'Reduzca el tamaño del modelo o las capas solicitadas.';
    return 'Revise el modelo y la configuración indicada; NodoBoard no realizará correcciones automáticas.';
  }

  private asRecord(value: unknown): Record<string, unknown> | null {
    return value && typeof value === 'object' && !Array.isArray(value)
      ? value as Record<string, unknown> : null;
  }
}
