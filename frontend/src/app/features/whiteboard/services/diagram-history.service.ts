import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Subject, firstValueFrom, timeout } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { HistoryCommand } from '../utils/history-command.utils';
import { WhiteboardSocketService } from './whiteboard-socket.service';

export interface DiagramHistory {
  proyecto_id: number; revision: number; canUndo: boolean; canRedo: boolean; limit: number;
  operations: { operation_id: string; description: string; status: string; confirmed_revision: number }[];
}
export interface HistoryResult {
  exito: boolean; revision: number; proyecto_id: number; mensaje: string; warnings: string[]; history: DiagramHistory;
}

/** Estado de interfaz por página. Django es la única autoridad de reversibilidad. */
@Injectable()
export class DiagramHistoryService {
  private readonly http = inject(HttpClient);
  private readonly socket = inject(WhiteboardSocketService);
  private projectId = 0;
  private generation = 0;
  private loadSequence = 0;
  private pendingRequest: { request_id: string; expected_revision: number; command: HistoryCommand } | null = null;
  public readonly state$ = new BehaviorSubject<DiagramHistory | null>(null);
  public readonly busy$ = new BehaviorSubject(false);
  public readonly cancelAssistant$ = new Subject<void>();
  public readonly confirmed$ = new Subject<HistoryResult>();
  public readonly messages$ = new Subject<{ text: string; error: boolean }>();
  public get canUndo(): boolean { return !!this.state$.value?.canUndo; }
  public get canRedo(): boolean { return !!this.state$.value?.canRedo; }

  public async loadHistory(projectId = this.projectId): Promise<void> {
    if (projectId !== this.projectId) this.clearLocalState();
    this.projectId = projectId;
    const generation = this.generation;
    const sequence = ++this.loadSequence;
    try {
      const state = await firstValueFrom(this.http.get<DiagramHistory>(this.url).pipe(timeout(20_000)));
      if (generation === this.generation && sequence === this.loadSequence && state.proyecto_id === this.projectId) this.state$.next(state);
    } catch {
      if (generation === this.generation) this.messages$.next({ text: 'No se pudo consultar tu historial persistente.', error: true });
    }
  }

  public async execute(command: HistoryCommand): Promise<void> {
    if (this.busy$.value || !this.projectId) return;
    this.cancelAssistant$.next();
    this.busy$.next(true);
    const generation = this.generation;
    try {
      await this.socket.esperarGuardadoConfirmado();
      if (generation !== this.generation) return;
      // Una respuesta perdida se consulta con exactamente el mismo contenido/ID.
      const pending = this.pendingRequest;
      const request = pending || { request_id: this.nuevoRequestId(), expected_revision: this.socket.revisionActual, command };
      this.pendingRequest = request;
      const result = await firstValueFrom(this.http.post<HistoryResult>(this.url, request).pipe(timeout(20_000)));
      if (generation !== this.generation || result.proyecto_id !== this.projectId) return;
      this.pendingRequest = null;
      this.state$.next(result.history);
      this.confirmed$.next(result);
      this.messages$.next({ text: [result.mensaje, ...(result.warnings || [])].join(' '), error: false });
      if (pending) this.messages$.next({ text: 'Se recuperó la confirmación de la solicitud anterior. Puedes enviar la siguiente acción.', error: false });
    } catch (error) {
      if (generation !== this.generation) return;
      const err = error as HttpErrorResponse;
      if (err.status && err.status < 500) this.pendingRequest = null;
      if (err.error?.codigo === 'stale_revision') this.socket.registrarConflictoRevision(err.error.current_revision, err.error.mensaje);
      this.messages$.next({ text: err.error?.mensaje || (error instanceof Error ? error.message : 'No se confirmó la operación. Reintenta para recuperar su resultado.'), error: true });
      await this.loadHistory();
    } finally {
      if (generation === this.generation) this.busy$.next(false);
    }
  }

  public clearLocalState(): void {
    this.generation++;
    this.projectId = 0;
    this.pendingRequest = null;
    this.state$.next(null);
    this.busy$.next(false);
    this.cancelAssistant$.next();
  }

  private nuevoRequestId(): string {
    const cryptoApi = globalThis.crypto;
    if (typeof cryptoApi?.randomUUID === 'function') return `history-${cryptoApi.randomUUID()}`;
    return `history-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }

  private get url(): string { return `${environment.apiUrl}/modelado/proyectos/${this.projectId}/historial/`; }
}
