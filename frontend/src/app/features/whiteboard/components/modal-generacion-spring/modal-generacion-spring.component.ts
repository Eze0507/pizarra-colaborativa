import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  OpcionesGeneracionSpring,
  SolicitudGeneracionSpring
} from '../../interfaces/generador.interface';
import { normalizarNombreProyectoSpring } from '../../utils/spring-generation.utils';


export type ConfiguracionGeneracionSpring = Omit<SolicitudGeneracionSpring, 'expected_revision'>;

const PROJECT_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const PACKAGE_SEGMENT = /^[a-z][a-z0-9_]*$/;
const RESERVED = new Set([
  'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
  'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
  'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
  'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new',
  'package', 'private', 'protected', 'public', 'return', 'short', 'static',
  'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
  'transient', 'try', 'void', 'volatile', 'while', 'con', 'prn', 'aux', 'nul'
]);

@Component({
  selector: 'app-modal-generacion-spring',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './modal-generacion-spring.component.html',
  styleUrls: ['./modal-generacion-spring.component.css']
})
export class ModalGeneracionSpringComponent implements OnChanges {
  public readonly capas: { key: keyof OpcionesGeneracionSpring; label: string }[] = [
    { key: 'modelo', label: 'Modelo' },
    { key: 'repositorio', label: 'Repositorio' },
    { key: 'servicio', label: 'Servicio' },
    { key: 'controlador', label: 'Controlador' }
  ];
  @Input() public visible = false;
  @Input() public generando = false;
  @Input() public puedeGenerar = false;
  @Input() public puedeGuardar = false;
  @Input() public motivoBloqueo = '';
  @Input() public nombreInicial = '';
  @Input() public paqueteInicial = '';
  @Input() public errorServidor: string | null = null;

  @Output() public readonly cerrar = new EventEmitter<void>();
  @Output() public readonly guardar = new EventEmitter<void>();
  @Output() public readonly generar = new EventEmitter<ConfiguracionGeneracionSpring>();

  public nombreProyecto = '';
  public paqueteBase = '';
  public opciones: OpcionesGeneracionSpring = this.opcionesIniciales();
  public mensajeOpciones = '';

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible']?.currentValue && !changes['visible']?.previousValue) {
      this.nombreProyecto = this.nombreInicial;
      this.paqueteBase = this.paqueteInicial;
      this.opciones = this.opcionesIniciales();
      this.mensajeOpciones = '';
    }
  }

  public cambiarOpcion(nombre: keyof OpcionesGeneracionSpring, activa: boolean): void {
    this.opciones = { ...this.opciones, [nombre]: activa };
    const orden: (keyof OpcionesGeneracionSpring)[] = [
      'modelo', 'repositorio', 'servicio', 'controlador'
    ];
    const index = orden.indexOf(nombre);
    if (activa) {
      for (let i = 0; i < index; i += 1) this.opciones[orden[i]] = true;
      this.mensajeOpciones = index > 0
        ? 'Se activaron las capas requeridas por la selección.' : '';
    } else {
      for (let i = index + 1; i < orden.length; i += 1) this.opciones[orden[i]] = false;
      this.mensajeOpciones = index < orden.length - 1
        ? 'Se desactivaron las capas que dependían de esta selección.' : '';
    }
    this.opciones = { ...this.opciones };
  }

  public enviar(): void {
    if (!this.formularioValido || !this.puedeGenerar || this.generando) return;
    this.generar.emit({
      nombre_proyecto: this.nombreProyecto,
      paquete_base: this.paqueteBase,
      opciones: { ...this.opciones }
    });
  }

  public normalizarNombreProyecto(): void {
    this.nombreProyecto = normalizarNombreProyectoSpring(this.nombreProyecto);
  }

  public get errorNombre(): string {
    if (!this.nombreProyecto) return 'El nombre del proyecto es obligatorio.';
    if (this.nombreProyecto.length > 64) return 'El nombre no puede superar 64 caracteres.';
    if (!PROJECT_PATTERN.test(this.nombreProyecto)) {
      return 'Use minúsculas, números y guiones; debe comenzar con una letra.';
    }
    if (RESERVED.has(this.nombreProyecto)) return 'El nombre está reservado.';
    return '';
  }

  public get errorPaquete(): string {
    if (!this.paqueteBase) return 'El paquete base es obligatorio.';
    if (this.paqueteBase.length > 200) return 'El paquete no puede superar 200 caracteres.';
    const segments = this.paqueteBase.split('.');
    if (segments.length < 2) return 'El paquete debe contener al menos dos segmentos.';
    if (segments.some(segment => !PACKAGE_SEGMENT.test(segment) || RESERVED.has(segment))) {
      return 'Cada segmento debe ser Java válido, en minúsculas y no reservado.';
    }
    return '';
  }

  public get formularioValido(): boolean {
    return !this.errorNombre && !this.errorPaquete && this.opcionesCoherentes;
  }

  private get opcionesCoherentes(): boolean {
    return (!this.opciones.repositorio || this.opciones.modelo)
      && (!this.opciones.servicio || this.opciones.repositorio)
      && (!this.opciones.controlador || this.opciones.servicio);
  }

  private opcionesIniciales(): OpcionesGeneracionSpring {
    return { modelo: true, repositorio: false, servicio: false, controlador: false };
  }
}
