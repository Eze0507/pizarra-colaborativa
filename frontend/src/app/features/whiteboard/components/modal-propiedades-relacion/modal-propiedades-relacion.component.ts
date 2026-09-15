import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RelacionDiagrama } from '../../interfaces/diagrama.interface';

export interface GuardarPropiedadesRelacionPayload {
  relacionId: number;
  nombre: string;
  cardinalidadOrigen: string;
  cardinalidadDestino: string;
}

@Component({
  selector: 'app-modal-propiedades-relacion',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './modal-propiedades-relacion.component.html',
  styleUrls: ['./modal-propiedades-relacion.component.css']
})
export class ModalPropiedadesRelacionComponent implements OnChanges {
  @Input() public visible = false;
  @Input() public relacion: RelacionDiagrama | null = null;
  @Input() public nombreOrigen = 'Origen';
  @Input() public nombreDestino = 'Destino';

  @Output() public readonly guardar = new EventEmitter<GuardarPropiedadesRelacionPayload>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public nombreRelacion = '';
  public cardinalidadOrigen = '1';
  public cardinalidadDestino = '0..*';
  public esComposicion = false;
  public tipoTexto = 'Asociación';

  public readonly presetsCardinalidad: string[] = ['1', '0..1', '1..*', '0..*', '*'];

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible && this.relacion) {
      this.cargarDatos(this.relacion);
    } else if (changes['relacion'] && this.relacion && this.visible) {
      this.cargarDatos(this.relacion);
    }
  }

  private cargarDatos(relacion: RelacionDiagrama): void {
    this.nombreRelacion = relacion.nombre_relacion || '';
    this.cardinalidadOrigen = relacion.cardinalidad_origen || '1';
    this.cardinalidadDestino = relacion.cardinalidad_destino || '0..*';
    this.esComposicion = relacion.tipo === 'composicion' || !!relacion.origen_bloqueado;

    switch (relacion.tipo) {
      case 'asociacion':
        this.tipoTexto = 'Asociación';
        break;
      case 'agregacion':
        this.tipoTexto = 'Agregación';
        break;
      case 'composicion':
        this.tipoTexto = 'Composición';
        break;
      case 'herencia':
        this.tipoTexto = 'Herencia';
        break;
      default:
        this.tipoTexto = 'Relación';
        break;
    }
  }

  public seleccionarPresetOrigen(valor: string): void {
    if (this.esComposicion) return;
    this.cardinalidadOrigen = valor;
  }

  public seleccionarPresetDestino(valor: string): void {
    this.cardinalidadDestino = valor;
  }

  public onGuardar(): void {
    if (!this.relacion) return;

    this.guardar.emit({
      relacionId: this.relacion.id,
      nombre: this.nombreRelacion.trim(),
      cardinalidadOrigen: this.esComposicion ? '1' : this.cardinalidadOrigen.trim(),
      cardinalidadDestino: this.cardinalidadDestino.trim()
    });
  }

  public onCancelar(): void {
    this.cancelar.emit();
  }
}
