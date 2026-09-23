import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnChanges,
  SimpleChanges,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import {
  ProyectoDiagrama,
  EstadoConexion,
  UsuarioConectado
} from '../../interfaces/diagrama.interface';
import {
  DiagramaGeneradoPayload
} from '../../interfaces/asistente-ia.interface';
import { AsistenteIaService } from '../../services/asistente-ia.service';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';

export type PestanaSidebar = 'toolbox' | 'ia';

@Component({
  selector: 'app-sidebar-pizarra',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sidebar-pizarra.component.html',
  styleUrls: ['./sidebar-pizarra.component.css']
})
export class SidebarPizarraComponent implements OnInit, OnChanges {
  private readonly asistenteIaService = inject(AsistenteIaService);
  private readonly toastService = inject(ToastNotificationService);

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

  // Asistente IA (Boceto a Diagrama)
  @Output() public readonly diagramaIAGenerado = new EventEmitter<DiagramaGeneradoPayload>();

  // Acciones globales del pie
  @Output() public readonly generarCodigo = new EventEmitter<void>();
  @Output() public readonly exportarImagen = new EventEmitter<void>();
  @Output() public readonly exportarXml = new EventEmitter<void>();
  @Output() public readonly importarXml = new EventEmitter<File>();
  @Output() public readonly volverDashboard = new EventEmitter<void>();
  @Output() public readonly cerrarSesion = new EventEmitter<void>();
  @Output() public readonly toggleTema = new EventEmitter<void>();

  // Estado visual interno del sidebar
  public colapsado = false;
  public pestanaActiva: PestanaSidebar = 'toolbox';
  public editandoNombre = false;
  public nombreProyectoInput = '';

  // Estado del Boceto a Diagrama
  public archivoSeleccionado: File | null = null;
  public previsualizacionUrl: string | null = null;
  public instruccionesIa = '';
  public cargandoIa = false;
  public mensajeEstadoIa = '';
  public errorIa: string | null = null;
  public arrastrandoArchivo = false;

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

  // ── Asistente IA: Manejo de Boceto / Imagen ──

  public onArchivoSeleccionado(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    this.procesarArchivo(input.files[0]);
  }

  public onDragOverArchivo(evento: DragEvent): void {
    evento.preventDefault();
    this.arrastrandoArchivo = true;
  }

  public onDragLeaveArchivo(): void {
    this.arrastrandoArchivo = false;
  }

  public onDropArchivo(evento: DragEvent): void {
    evento.preventDefault();
    this.arrastrandoArchivo = false;
    if (evento.dataTransfer && evento.dataTransfer.files.length > 0) {
      this.procesarArchivo(evento.dataTransfer.files[0]);
    }
  }

  private procesarArchivo(archivo: File): void {
    if (!archivo.type.startsWith('image/')) {
      this.errorIa = 'El archivo seleccionado debe ser una imagen válida (JPG, PNG, WEBP).';
      return;
    }
    this.errorIa = null;
    this.archivoSeleccionado = archivo;
    if (this.previsualizacionUrl) {
      URL.revokeObjectURL(this.previsualizacionUrl);
    }
    this.previsualizacionUrl = URL.createObjectURL(archivo);
  }

  public limpiarImagen(): void {
    if (this.previsualizacionUrl) {
      URL.revokeObjectURL(this.previsualizacionUrl);
      this.previsualizacionUrl = null;
    }
    this.archivoSeleccionado = null;
    this.errorIa = null;
    this.mensajeEstadoIa = '';
  }

  public onGenerarDiagramaIA(): void {
    if (!this.archivoSeleccionado || this.cargandoIa) return;
    this.cargandoIa = true;
    this.errorIa = null;
    this.mensajeEstadoIa = 'Comprimiendo imagen...';

    this.asistenteIaService
      .comprimirImagen(this.archivoSeleccionado)
      .then((blobComprimido: Blob) => {
        this.mensajeEstadoIa = 'Analizando el boceto...';
        this.enviarImagenABackend(blobComprimido);
      })
      .catch(() => {
        this.mensajeEstadoIa = 'Analizando el boceto...';
        this.enviarImagenABackend(this.archivoSeleccionado!);
      });
  }

  private enviarImagenABackend(imagen: Blob | File): void {
    this.asistenteIaService
      .generarDiagramaDesdeImagen(imagen, this.instruccionesIa)
      .subscribe({
        next: (resp) => {
          this.mensajeEstadoIa = 'Construyendo diagrama...';
          const payload = this.asistenteIaService.normalizarRespuestaIA(resp);
          if (payload.entidades.length === 0) {
            this.errorIa = 'No se detectaron tablas o clases legibles en el boceto. Intenta con una toma más cercana.';
            this.cargandoIa = false;
            return;
          }
          this.diagramaIAGenerado.emit(payload);
          this.toastService.exito(
            `¡Diagrama generado! ${payload.entidades.length} entidades y ${payload.relaciones.length} relaciones.`
          );
          this.limpiarImagen();
          this.instruccionesIa = '';
          this.cargandoIa = false;
        },
        error: (err: HttpErrorResponse) => {
          this.cargandoIa = false;
          const msg = err.error?.error || 'No se pudo procesar la imagen del boceto. Verifique su conexión.';
          this.errorIa = msg;
          this.toastService.error(msg);
        }
      });
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

  public onSeleccionarArchivoXml(evento: Event): void {
    const input = evento.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const archivo = input.files[0];
      this.importarXml.emit(archivo);
      input.value = '';
    }
  }
}
