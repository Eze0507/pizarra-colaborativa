import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EntidadDiagrama, AtributoDiagrama } from '../../interfaces/diagrama.interface';

@Component({
  selector: 'app-modal-propiedades-entidad',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './modal-propiedades-entidad.component.html',
  styleUrls: ['./modal-propiedades-entidad.component.css']
})
export class ModalPropiedadesEntidadComponent implements OnChanges {
  @Input() public visible = false;
  @Input() public entidad: EntidadDiagrama | null = null;

  @Output() public readonly guardar = new EventEmitter<EntidadDiagrama>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public nombre = '';
  public estado: 'activo' | 'bloqueado' | 'papelera' = 'activo';
  public atributos: AtributoDiagrama[] = [];
  public errorNombre: string | null = null;

  public readonly tiposDisponibles: Array<AtributoDiagrama['tipo']> = [
    'string',
    'integer',
    'long',
    'double',
    'boolean',
    'date'
  ];

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible && this.entidad) {
      this.cargarDatos(this.entidad);
    } else if (changes['entidad'] && this.entidad && this.visible) {
      this.cargarDatos(this.entidad);
    }
  }

  private cargarDatos(entidad: EntidadDiagrama): void {
    this.nombre = entidad.nombre || '';
    this.estado = entidad.estado || 'activo';
    this.errorNombre = null;

    if (entidad.atributos && Array.isArray(entidad.atributos)) {
      this.atributos = entidad.atributos.map(a => ({
        id: a.id,
        nombre: a.nombre,
        tipo: a.tipo || 'string',
        es_clave: !!a.es_clave,
        es_nulo: !!a.es_nulo,
        orden: a.orden || 1
      }));
    } else {
      this.atributos = [];
    }
  }

  public agregarAtributo(): void {
    const nuevoOrden = this.atributos.length + 1;
    const nuevoId = -Date.now() - Math.floor(Math.random() * 1000);
    this.atributos.push({
      id: nuevoId,
      nombre: '',
      tipo: 'string',
      es_clave: false,
      es_nulo: false,
      orden: nuevoOrden
    });
  }

  public eliminarAtributo(index: number): void {
    this.atributos.splice(index, 1);
    this.atributos.forEach((attr, idx) => {
      attr.orden = idx + 1;
    });
  }

  public onGuardar(): void {
    const nombreLimpio = this.nombre.trim();
    if (!nombreLimpio) {
      this.errorNombre = 'El nombre de la entidad es obligatorio.';
      return;
    }

    if (!this.entidad) return;

    // Normalizar atributos
    const atributosLimpios: AtributoDiagrama[] = this.atributos
      .filter(a => a.nombre && a.nombre.trim().length > 0)
      .map((a, idx) => ({
        id: a.id,
        nombre: a.nombre.trim(),
        tipo: a.tipo,
        es_clave: a.es_clave,
        es_nulo: a.es_nulo,
        orden: idx + 1
      }));

    const entidadActualizada: EntidadDiagrama = {
      ...this.entidad,
      nombre: nombreLimpio,
      estado: this.estado,
      atributos: atributosLimpios
    };

    this.guardar.emit(entidadActualizada);
  }

  public onCancelar(): void {
    this.cancelar.emit();
  }
}
