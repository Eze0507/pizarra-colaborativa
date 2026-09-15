import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  OnChanges,
  SimpleChanges,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, Subscription, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, catchError, finalize } from 'rxjs/operators';

import { WhiteboardApiService } from '../../services/whiteboard-api.service';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';
import { UsuarioBusqueda, ColaboradorProyecto } from '../../interfaces/colaborador.interface';

@Component({
  selector: 'app-modal-colaboradores',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './modal-colaboradores.component.html',
  styleUrls: ['./modal-colaboradores.component.css']
})
export class ModalColaboradoresComponent implements OnInit, OnDestroy, OnChanges {
  private readonly apiService = inject(WhiteboardApiService);
  private readonly toastService = inject(ToastNotificationService);

  @Input() public visible = false;
  @Input() public proyectoId = 0;
  @Input() public esPropietario = false;
  @Input() public modoOscuro = false;

  @Output() public readonly cerrar = new EventEmitter<void>();

  // ── Sección 1: Búsqueda e Invitación ──
  public terminoBusqueda = '';
  public cargandoBusqueda = false;
  public resultadosBusqueda: UsuarioBusqueda[] = [];
  public mostrarDropdown = false;
  public usuarioSeleccionado: UsuarioBusqueda | null = null;
  public confirmandoInvitacion = false;
  public enviandoInvitacion = false;

  // ── Sección 2: Lista de Colaboradores ──
  public colaboradores: ColaboradorProyecto[] = [];
  public cargandoColaboradores = false;
  public reenviandoId: number | null = null;
  public eliminandoId: number | null = null;
  public confirmandoEliminarId: number | null = null;

  private readonly busquedaSubject = new Subject<string>();
  private readonly subscriptions = new Subscription();

  public ngOnInit(): void {
    this.subscriptions.add(
      this.busquedaSubject.pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap(term => {
          const limpio = term.trim();
          if (limpio.length < 2) {
            this.cargandoBusqueda = false;
            this.resultadosBusqueda = [];
            this.mostrarDropdown = false;
            return of([]);
          }
          this.cargandoBusqueda = true;
          return this.apiService.buscarUsuarios(limpio).pipe(
            catchError(() => {
              this.toastService.error('Error al buscar usuarios');
              return of([]);
            }),
            finalize(() => {
              this.cargandoBusqueda = false;
            })
          );
        })
      ).subscribe(usuarios => {
        this.resultadosBusqueda = usuarios;
        this.mostrarDropdown = usuarios.length > 0;
      })
    );
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.resetearFormularioBusqueda();
      this.cargarColaboradores();
    }
  }

  public onBuscarInput(val: string): void {
    this.terminoBusqueda = val;
    this.usuarioSeleccionado = null;
    this.confirmandoInvitacion = false;
    this.busquedaSubject.next(val);
  }

  public seleccionarUsuario(usuario: UsuarioBusqueda): void {
    this.usuarioSeleccionado = usuario;
    this.terminoBusqueda = `${usuario.username} (${usuario.email})`;
    this.mostrarDropdown = false;
    this.resultadosBusqueda = [];
    this.confirmandoInvitacion = false;
  }

  public deseleccionarUsuario(): void {
    this.usuarioSeleccionado = null;
    this.terminoBusqueda = '';
    this.confirmandoInvitacion = false;
    this.mostrarDropdown = false;
  }

  public abrirConfirmacionInvitacion(): void {
    if (!this.usuarioSeleccionado || this.enviandoInvitacion) return;
    this.confirmandoInvitacion = true;
  }

  public cancelarConfirmacionInvitacion(): void {
    this.confirmandoInvitacion = false;
  }

  public enviarInvitacion(): void {
    if (!this.usuarioSeleccionado || this.enviandoInvitacion || !this.proyectoId) return;

    this.enviandoInvitacion = true;
    const datos = { email: this.usuarioSeleccionado.email, username: this.usuarioSeleccionado.username };

    this.apiService.invitarColaborador(this.proyectoId, datos).pipe(
      finalize(() => {
        this.enviandoInvitacion = false;
      })
    ).subscribe({
      next: (res) => {
        this.toastService.exito(res.detail || 'Invitación enviada exitosamente');
        this.resetearFormularioBusqueda();
        this.cargarColaboradores();
      },
      error: (err) => {
        const errorMsg = err.error?.detail || err.error?.non_field_errors?.[0] || 'Error al enviar la invitación';
        this.toastService.error(errorMsg);
      }
    });
  }

  public cargarColaboradores(): void {
    if (!this.proyectoId) return;

    this.cargandoColaboradores = true;
    this.apiService.obtenerColaboradores(this.proyectoId).pipe(
      finalize(() => {
        this.cargandoColaboradores = false;
      })
    ).subscribe({
      next: (colabs) => {
        this.colaboradores = colabs;
      },
      error: () => {
        this.toastService.error('Error al cargar la lista de colaboradores');
      }
    });
  }

  public reenviarInvitacion(colaborador: ColaboradorProyecto): void {
    if (this.reenviandoId !== null || !this.proyectoId) return;

    this.reenviandoId = colaborador.id;
    this.apiService.reenviarInvitacion(this.proyectoId, colaborador.id).pipe(
      finalize(() => {
        this.reenviandoId = null;
      })
    ).subscribe({
      next: (res) => {
        this.toastService.exito(res.detail || 'Invitación reenviada exitosamente');
      },
      error: (err) => {
        const errorMsg = err.error?.detail || 'Error al reenviar la invitación';
        this.toastService.error(errorMsg);
      }
    });
  }

  public solicitarEliminarColaborador(colaboradorId: number): void {
    if (this.confirmandoEliminarId === colaboradorId) {
      this.ejecutarEliminarColaborador(colaboradorId);
    } else {
      this.confirmandoEliminarId = colaboradorId;
    }
  }

  public cancelarEliminacion(): void {
    this.confirmandoEliminarId = null;
  }

  private ejecutarEliminarColaborador(colaboradorId: number): void {
    if (this.eliminandoId !== null || !this.proyectoId) return;

    this.eliminandoId = colaboradorId;
    this.apiService.eliminarColaborador(this.proyectoId, colaboradorId).pipe(
      finalize(() => {
        this.eliminandoId = null;
        this.confirmandoEliminarId = null;
      })
    ).subscribe({
      next: (res) => {
        this.toastService.exito(res.detail || 'Colaborador eliminado exitosamente');
        this.cargarColaboradores();
      },
      error: (err) => {
        const errorMsg = err.error?.detail || 'Error al eliminar el colaborador';
        this.toastService.error(errorMsg);
      }
    });
  }

  public onCerrar(): void {
    this.resetearFormularioBusqueda();
    this.cerrar.emit();
  }

  private resetearFormularioBusqueda(): void {
    this.terminoBusqueda = '';
    this.usuarioSeleccionado = null;
    this.confirmandoInvitacion = false;
    this.enviandoInvitacion = false;
    this.resultadosBusqueda = [];
    this.mostrarDropdown = false;
    this.confirmandoEliminarId = null;
  }
}
