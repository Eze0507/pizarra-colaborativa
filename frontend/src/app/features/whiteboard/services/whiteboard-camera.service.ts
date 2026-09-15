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

  private onWheelHandler = (evt: WheelEvent) => this.onWheel(evt);
  private onWindowMouseMoveRef = (evt: MouseEvent) => this.onWindowMouseMove(evt);
  private onWindowMouseUpRef = () => this.onWindowMouseUp();

  public get zoomNivel(): number {
    return this._zoomNivel$.getValue();
  }

  public conectar(paper: joint.dia.Paper, container: HTMLElement): void {
    this.paper = paper;
    this.lienzoContainer = container;

    container.addEventListener('wheel', this.onWheelHandler, { passive: false });
    window.addEventListener('mousemove', this.onWindowMouseMoveRef);
    window.addEventListener('mouseup', this.onWindowMouseUpRef);
  }

  public desconectar(): void {
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

    const m = this.paper.matrix();
    this.paper.translate((m.e || 0) + dx, (m.f || 0) + dy);
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

    this.cerrarModales$.next();

    const delta = evt.deltaY;
    if (delta === 0) return;

    const zoomFactor = delta < 0 ? 1.15 : 1 / 1.15;
    const currentScale = this.paper.scale().sx;
    let targetScale = currentScale * zoomFactor;

    targetScale = Math.min(Math.max(targetScale, 0.2), 3.0);

    if (Math.abs(targetScale - currentScale) < 0.001) return;

    const localPoint = this.paper.clientToLocalPoint({ x: evt.clientX, y: evt.clientY });
    this.paper.scaleUniformAtPoint(targetScale, localPoint);

    this._zoomNivel$.next(Math.round(targetScale * 100));
  }

  public zoomIn(): void {
    this.aplicarZoomAlCentro(1.15);
  }

  public zoomOut(): void {
    this.aplicarZoomAlCentro(1 / 1.15);
  }

  public zoomReset(): void {
    if (!this.paper) return;
    const currentScale = this.paper.scale().sx;
    if (Math.abs(currentScale - 1) < 0.001) return;

    this.aplicarZoomAlCentro(1 / currentScale);
    this._zoomNivel$.next(100);
  }

  private aplicarZoomAlCentro(factor: number): void {
    if (!this.paper || !this.lienzoContainer) return;
    this.cerrarModales$.next();

    const currentScale = this.paper.scale().sx;
    let targetScale = currentScale * factor;
    targetScale = Math.min(Math.max(targetScale, 0.2), 3.0);
    if (Math.abs(targetScale - currentScale) < 0.001) return;

    const rect = this.lienzoContainer.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const centerLocal = this.paper.clientToLocalPoint({ x: centerX, y: centerY });

    this.paper.scaleUniformAtPoint(targetScale, centerLocal);
    this._zoomNivel$.next(Math.round(targetScale * 100));
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
