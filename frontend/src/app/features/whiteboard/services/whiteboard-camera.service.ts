import { Injectable } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';
import * as joint from '@joint/core';

@Injectable()
export class WhiteboardCameraService {
  private paper: joint.dia.Paper | null = null;
  private lienzoContainer: HTMLElement | null = null;

  private readonly _zoomNivel$ = new BehaviorSubject<number>(100);
  public readonly zoomNivel$ = this._zoomNivel$.asObservable();

  public readonly cerrarModales$ = new Subject<void>();

  private isPanning = false;
  private panStartX = 0;
  private panStartY = 0;

  private rafPanId: number | null = null;
  private pendingPanDx = 0;
  private pendingPanDy = 0;

  private rafZoomId: number | null = null;
  private targetScale = 1;
  private zoomPivotClient = { x: 0, y: 0 };
  private debounceModalesTimer: ReturnType<typeof setTimeout> | null = null;

  private onWheelHandler = (evt: WheelEvent) => this.onWheel(evt);
  private onWindowMouseMoveRef = (evt: MouseEvent) => this.onWindowMouseMove(evt);
  private onWindowMouseUpRef = () => this.onWindowMouseUp();

  public get zoomNivel(): number {
    return this._zoomNivel$.getValue();
  }

  public conectar(paper: joint.dia.Paper, container: HTMLElement): void {
    this.paper = paper;
    this.lienzoContainer = container;
    this.targetScale = paper.scale().sx || 1;

    container.addEventListener('wheel', this.onWheelHandler, { passive: false });
    window.addEventListener('mousemove', this.onWindowMouseMoveRef);
    window.addEventListener('mouseup', this.onWindowMouseUpRef);
  }

  public desconectar(): void {
    if (this.rafZoomId !== null) {
      cancelAnimationFrame(this.rafZoomId);
      this.rafZoomId = null;
    }
    if (this.rafPanId !== null) {
      cancelAnimationFrame(this.rafPanId);
      this.rafPanId = null;
    }
    if (this.debounceModalesTimer !== null) {
      clearTimeout(this.debounceModalesTimer);
      this.debounceModalesTimer = null;
    }
    if (this.lienzoContainer) {
      this.lienzoContainer.removeEventListener('wheel', this.onWheelHandler);
    }
    window.removeEventListener('mousemove', this.onWindowMouseMoveRef);
    window.removeEventListener('mouseup', this.onWindowMouseUpRef);
    this.paper = null;
    this.lienzoContainer = null;
  }

  public iniciarPaneo(evt: MouseEvent): void {
    this.cerrarModales$.next();
    this.isPanning = true;
    this.panStartX = evt.clientX;
    this.panStartY = evt.clientY;
    this.pendingPanDx = 0;
    this.pendingPanDy = 0;
    if (this.lienzoContainer) {
      this.lienzoContainer.style.cursor = 'grabbing';
    }
  }

  private onWindowMouseMove(evt: MouseEvent): void {
    if (!this.isPanning || !this.paper) return;
    const dx = evt.clientX - this.panStartX;
    const dy = evt.clientY - this.panStartY;
    this.panStartX = evt.clientX;
    this.panStartY = evt.clientY;

    this.pendingPanDx += dx;
    this.pendingPanDy += dy;

    if (this.rafPanId === null) {
      this.rafPanId = requestAnimationFrame(() => {
        this.rafPanId = null;
        if (!this.paper) return;
        const m = this.paper.matrix();
        this.paper.translate((m.e || 0) + this.pendingPanDx, (m.f || 0) + this.pendingPanDy);
        this.pendingPanDx = 0;
        this.pendingPanDy = 0;
      });
    }
  }

  private onWindowMouseUp(): void {
    if (this.isPanning) {
      this.isPanning = false;
      if (this.lienzoContainer) {
        this.lienzoContainer.style.cursor = 'default';
      }
    }
  }

  private onWheel(evt: WheelEvent): void {
    evt.preventDefault();
    if (!this.paper) return;

    // Cerrar modales una sola vez al inicio del gesto de zoom
    if (!this.debounceModalesTimer) {
      this.cerrarModales$.next();
    } else {
      clearTimeout(this.debounceModalesTimer);
    }
    this.debounceModalesTimer = setTimeout(() => {
      this.debounceModalesTimer = null;
    }, 200);

    let deltaY = evt.deltaY;
    if (evt.deltaMode === 1) {
      deltaY *= 24; // Modo líneas (rueda de mouse clásica)
    } else if (evt.deltaMode === 2) {
      deltaY *= 400; // Modo páginas
    }

    if (deltaY === 0) return;

    // Normalización exponencial proporcional al desplazamiento real
    const deltaAcotado = Math.max(-100, Math.min(100, deltaY));
    const factor = Math.exp(-deltaAcotado * 0.0018);

    const currentScale = this.rafZoomId !== null ? this.targetScale : this.paper.scale().sx;
    let nextScale = currentScale * factor;
    nextScale = Math.min(Math.max(nextScale, 0.2), 3.0);

    if (Math.abs(nextScale - currentScale) < 0.0005) return;

    this.targetScale = nextScale;
    this.zoomPivotClient = { x: evt.clientX, y: evt.clientY };

    if (this.rafZoomId === null) {
      this.rafZoomId = requestAnimationFrame(() => {
        this.rafZoomId = null;
        if (!this.paper) return;
        const localPoint = this.paper.clientToLocalPoint(this.zoomPivotClient);
        this.paper.scaleUniformAtPoint(this.targetScale, localPoint);

        const nuevoNivel = Math.round(this.targetScale * 100);
        if (nuevoNivel !== this._zoomNivel$.getValue()) {
          this._zoomNivel$.next(nuevoNivel);
        }
      });
    }
  }

  public zoomIn(): void {
    this.animarZoomAlCentro(1.2);
  }

  public zoomOut(): void {
    this.animarZoomAlCentro(1 / 1.2);
  }

  public zoomReset(): void {
    if (!this.paper) return;
    const currentScale = this.paper.scale().sx;
    if (Math.abs(currentScale - 1) < 0.01) return;
    this.animarZoomAlCentro(1 / currentScale);
  }

  private animarZoomAlCentro(factor: number): void {
    if (!this.paper || !this.lienzoContainer) return;
    this.cerrarModales$.next();

    const startScale = this.paper.scale().sx;
    const endScale = Math.min(Math.max(startScale * factor, 0.2), 3.0);
    if (Math.abs(endScale - startScale) < 0.005) return;

    const rect = this.lienzoContainer.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const startTime = performance.now();
    const duration = 120; // 120ms: transición ultra rápida y fluida

    const step = (now: number) => {
      if (!this.paper) return;
      const progress = Math.min((now - startTime) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = startScale + (endScale - startScale) * ease;

      const centerLocal = this.paper.clientToLocalPoint({ x: centerX, y: centerY });
      this.paper.scaleUniformAtPoint(current, centerLocal);
      this.targetScale = current;

      const nuevoNivel = Math.round(current * 100);
      if (nuevoNivel !== this._zoomNivel$.getValue()) {
        this._zoomNivel$.next(nuevoNivel);
      }

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        this._zoomNivel$.next(Math.round(endScale * 100));
      }
    };

    requestAnimationFrame(step);
  }

  public calcularCentroVisible(): { x: number; y: number } {
    if (!this.paper || !this.lienzoContainer) return { x: 100, y: 100 };
    const rect = this.lienzoContainer.getBoundingClientRect();
    const clientCenterX = rect.left + rect.width / 2;
    const clientCenterY = rect.top + rect.height / 2;
    const localCenter = this.paper.clientToLocalPoint({ x: clientCenterX, y: clientCenterY });
    return { x: Math.round(localCenter.x), y: Math.round(localCenter.y) };
  }
}
