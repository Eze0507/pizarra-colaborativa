import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProyectoDiagrama, EstadoConexion, UsuarioConectado } from '../../interfaces/diagrama.interface';

export type PestanaSidebar = 'toolbox' | 'ia';

@Component({
  selector: 'app-sidebar-pizarra',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sidebar-pizarra.component.html',
  styleUrls: ['./sidebar-pizarra.component.css']
})
export class SidebarPizarraComponent implements OnInit, OnChanges {
  @Input() public proyecto: ProyectoDiagrama | null = null;
  @Input() public estadoConexion: EstadoConexion = 'desconectado';
  @Input() public estadoGuardado: 'guardado' | 'guardando' | 'error' = 'guardado';
  @Input() public modoOscuro = false;
  @Input() public usuariosConectados: UsuarioConectado[] = [];

  // Acciones de elementos y lienzo
  @Output() public readonly agregarEntidad = new EventEmitter<void>();
  @Output() public readonly agregarClaseAsociacion = new EventEmitter<void>();
  @Output() public readonly agregarNota = new EventEmitter<void>();

  // Cabecera y colaboración
  @Output() public readonly renombrarProyecto = new EventEmitter<string>();
  @Output() public readonly abrirColaboradores = new EventEmitter<void>();

  // Acciones globales del pie
  @Output() public readonly generarCodigo = new EventEmitter<void>();
  @Output() public readonly exportarImagen = new EventEmitter<void>();
  @Output() public readonly volverDashboard = new EventEmitter<void>();
  @Output() public readonly cerrarSesion = new EventEmitter<void>();
  @Output() public readonly toggleTema = new EventEmitter<void>();

  // Estado visual interno del sidebar
  public colapsado = false;
  public pestanaActiva: PestanaSidebar = 'toolbox';
  public editandoNombre = false;
  public nombreProyectoInput = '';

  public ngOnInit(): void {
    if (this.proyecto?.nombre) {
      this.nombreProyectoInput = this.proyecto.nombre;
    }
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['proyecto'] && this.proyecto?.nombre && !this.editandoNombre) {
      this.nombreProyectoInput = this.proyecto.nombre;
    }
  }

  // ── Colapso y Pestañas ──

  public toggleColapso(): void {
    this.colapsado = !this.colapsado;
  }

  public abrirEnPestana(pestana: PestanaSidebar): void {
    this.pestanaActiva = pestana;
    if (this.colapsado) {
      this.colapsado = false;
    }
  }

  public cambiarPestana(pestana: PestanaSidebar): void {
    this.pestanaActiva = pestana;
  }

  // ── Renombrado Editable de Proyecto ──

  public iniciarEdicionNombre(): void {
    this.nombreProyectoInput = this.proyecto?.nombre || '';
    this.editandoNombre = true;
  }

  public confirmarRenombrado(): void {
    if (!this.editandoNombre) return;
    const nuevo = this.nombreProyectoInput.trim();
    if (nuevo && nuevo !== this.proyecto?.nombre) {
      this.renombrarProyecto.emit(nuevo);
    } else {
      this.nombreProyectoInput = this.proyecto?.nombre || '';
    }
    this.editandoNombre = false;
  }

  public cancelarEdicionNombre(): void {
    this.nombreProyectoInput = this.proyecto?.nombre || '';
    this.editandoNombre = false;
  }

  // ── Drag & Drop de Herramientas al Lienzo ──

  public onDragStart(evt: DragEvent, tipo: 'entidad' | 'clase_asociacion' | 'nota'): void {
    if (evt.dataTransfer) {
      evt.dataTransfer.setData('application/json', JSON.stringify({ tipo }));
      evt.dataTransfer.setData('text/plain', tipo);
      evt.dataTransfer.effectAllowed = 'copy';
    }
  }

  // ── Avatares e Información de Usuarios Conectados ──

  public get usuariosVisibles(): UsuarioConectado[] {
    return this.usuariosConectados.slice(0, 3);
  }

  public get usuariosRestantesCount(): number {
    return Math.max(0, this.usuariosConectados.length - 3);
  }

  public obtenerIniciales(usuario: UsuarioConectado): string {
    if (usuario.first_name && usuario.first_name.trim().length > 0) {
      return usuario.first_name.slice(0, 2).toUpperCase();
    }
    if (usuario.username && usuario.username.trim().length > 0) {
      return usuario.username.slice(0, 2).toUpperCase();
    }
    return 'US';
  }

  public obtenerColorAvatar(usuario: UsuarioConectado): string {
    const paleta = [
      '#00A3FF', '#10B981', '#8B5CF6', '#F59E0B', '#EC4899', '#06B6D4'
    ];
    let hash = 0;
    const str = usuario.username || `${usuario.usuario_id}`;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return paleta[Math.abs(hash) % paleta.length];
  }

  // ── Getters de Estado ──

  public get etiquetaEstado(): string {
    const etiquetas: Record<EstadoConexion, string> = {
      conectando: 'Conectando...',
      conectado: 'En vivo',
      desconectado: 'Desconectado',
      error: 'Error conexión'
    };
    return etiquetas[this.estadoConexion];
  }

  public get claseEstado(): string {
    return `estado-${this.estadoConexion}`;
  }

  public get etiquetaGuardado(): string {
    switch (this.estadoGuardado) {
      case 'guardando': return 'Guardando...';
      case 'error':     return 'Error al guardar';
      case 'guardado':
      default:
        return 'Guardado';
    }
  }
}
