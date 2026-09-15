import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-controles-zoom',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './controles-zoom.component.html',
  styleUrls: ['./controles-zoom.component.css']
})
export class ControlesZoomComponent {
  @Input() public zoomNivel = 100;

  @Output() public readonly zoomIn = new EventEmitter<void>();
  @Output() public readonly zoomOut = new EventEmitter<void>();
  @Output() public readonly zoomReset = new EventEmitter<void>();

  public onZoomIn(): void {
    this.zoomIn.emit();
  }

  public onZoomOut(): void {
    this.zoomOut.emit();
  }

  public onZoomReset(): void {
    this.zoomReset.emit();
  }
}
