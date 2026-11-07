import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EntidadDiagrama, AtributoDiagrama, OperacionDiagrama, ParametroOperacionDiagrama, TipoClasificador, VisibilidadUML } from '../../interfaces/diagrama.interface';

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
  @Input() public clasificadores: EntidadDiagrama[] = [];

  @Output() public readonly guardar = new EventEmitter<EntidadDiagrama>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public nombre = '';
  public estado: 'activo' | 'bloqueado' | 'papelera' = 'activo';
  public atributos: AtributoDiagrama[] = [];
  public operaciones: OperacionDiagrama[] = [];
  public tipoClasificador: TipoClasificador = 'clase';
  public abstracto = false;
  public errorNombre: string | null = null;

  public readonly tiposDisponibles: string[] = [
    'string',
    'integer',
    'long',
    'double',
    'boolean',
    'date'
  ];
  public readonly visibilidades: VisibilidadUML[] = ['public', 'protected', 'private', 'package'];

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
    this.tipoClasificador = entidad.tipo_clasificador || 'clase';
    this.abstracto = !!entidad.abstracto;
    this.errorNombre = null;

    if (entidad.atributos && Array.isArray(entidad.atributos)) {
      this.atributos = entidad.atributos.map(a => ({
        id: a.id,
        nombre: a.nombre,
        tipo: a.tipo || 'string',
        tipo_referencia_id: a.tipo_referencia_id ?? null,
        visibilidad: a.visibilidad || 'private',
        es_estatico: !!a.es_estatico,
        valor_predeterminado: a.valor_predeterminado || '',
        es_clave: !!a.es_clave,
        es_nulo: !!a.es_nulo,
        orden: a.orden || 1
      }));
    } else {
      this.atributos = [];
    }
    this.operaciones = (entidad.operaciones || []).map(o => ({
      ...o,
      parametros: (o.parametros || []).map(p => ({ ...p }))
    }));
  }

  public agregarAtributo(): void {
    const nuevoOrden = this.atributos.length + 1;
    const nuevoId = -Date.now() - Math.floor(Math.random() * 1000);
    this.atributos.push({
      id: nuevoId,
      nombre: '',
      tipo: 'string',
      tipo_referencia_id: null,
      visibilidad: 'private',
      es_estatico: false,
      valor_predeterminado: '',
      es_clave: false,
      es_nulo: false,
      orden: nuevoOrden
    });
  }

  public agregarOperacion(): void {
    this.operaciones.push({
      id: -Date.now() - Math.floor(Math.random() * 1000), nombre: '', visibilidad: 'public',
      tipo_retorno: 'void', retorno_referencia_id: null, orden: this.operaciones.length + 1,
      es_estatico: false, es_abstracto: false, parametros: []
    });
  }

  public eliminarOperacion(index: number): void {
    this.operaciones.splice(index, 1);
    this.operaciones.forEach((o, i) => o.orden = i + 1);
  }

  public agregarParametro(operacion: OperacionDiagrama): void {
    operacion.parametros.push({ id: -Date.now() - Math.floor(Math.random() * 1000), nombre: '', tipo: 'string', tipo_referencia_id: null, orden: operacion.parametros.length + 1 });
  }

  public eliminarParametro(operacion: OperacionDiagrama, index: number): void {
    operacion.parametros.splice(index, 1);
    operacion.parametros.forEach((p, i) => p.orden = i + 1);
  }

  public usarReferencia(item: AtributoDiagrama | ParametroOperacionDiagrama, value: string): void {
    item.tipo_referencia_id = value ? Number(value) : null;
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
        tipo_referencia_id: a.tipo_referencia_id ?? null,
        visibilidad: a.visibilidad || 'private',
        es_estatico: !!a.es_estatico,
        valor_predeterminado: a.valor_predeterminado || '',
        es_clave: a.es_clave,
        es_nulo: a.es_nulo,
        orden: idx + 1
      }));

    const entidadActualizada: EntidadDiagrama = {
      ...this.entidad,
      nombre: nombreLimpio,
      estado: this.estado,
      tipo_clasificador: this.tipoClasificador,
      abstracto: this.tipoClasificador === 'interfaz' ? true : this.abstracto,
      atributos: atributosLimpios,
      operaciones: this.operaciones.filter(o => o.nombre.trim()).map((o, oi) => ({
        ...o, nombre: o.nombre.trim(), orden: oi + 1,
        parametros: o.parametros.filter(p => p.nombre.trim()).map((p, pi) => ({ ...p, nombre: p.nombre.trim(), orden: pi + 1 }))
      }))
    };

    this.guardar.emit(entidadActualizada);
  }

  public onCancelar(): void {
    this.cancelar.emit();
  }
}
