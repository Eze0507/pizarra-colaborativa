import { Component, OnInit, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ProjectsService } from '../../services/projects.service';
import { InvitacionesService } from '../../services/invitaciones.service';
import { Proyecto } from '../../interfaces/proyecto.interface';
import { ProjectCardComponent } from '../../components/project-card/project-card.component';
import { CreateProjectModalComponent } from '../../components/create-project-modal/create-project-modal.component';
import { DeleteProjectModalComponent } from '../../components/delete-project-modal/delete-project-modal.component';
import { SearchBarComponent } from '../../../../shared/components/search-bar/search-bar.component';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';

@Component({
  selector: 'app-projects-list-page',
  standalone: true,
  imports: [CommonModule, ProjectCardComponent, CreateProjectModalComponent, DeleteProjectModalComponent, SearchBarComponent],
  templateUrl: './projects-list.page.html',
  styleUrls: ['./projects-list.page.css']
})
export class ProjectsListPage implements OnInit {
  private readonly projectsService = inject(ProjectsService);
  private readonly invitacionesService = inject(InvitacionesService);
  private readonly toastService = inject(ToastNotificationService);
  private readonly destroyRef = inject(DestroyRef);

  public proyectos: Proyecto[] = [];
  public isLoading = true;
  public errorMessage: string | null = null;
  public isModalOpen = false;
  public isDeleteModalOpen = false;
  public projectToDelete: Proyecto | null = null;
  public searchTerm = '';

  public ngOnInit(): void {
    this.loadProyectos();

    // Recargar automáticamente la lista si se acepta una invitación desde el Header
    this.invitacionesService.invitacionAceptada$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.loadProyectos();
      });
  }

  public loadProyectos(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.projectsService.getProyectos().subscribe({
      next: (data: Proyecto[]) => {
        // Ordenar del más reciente al menos reciente por fecha_actualizacion
        this.proyectos = [...data].sort((a, b) => {
          const timeA = new Date(a.fecha_actualizacion).getTime();
          const timeB = new Date(b.fecha_actualizacion).getTime();
          return timeB - timeA;
        });
        this.isLoading = false;
      },
      error: (error: HttpErrorResponse) => {
        this.isLoading = false;
        if (error.error && typeof error.error.detail === 'string') {
          this.errorMessage = error.error.detail;
        } else {
          this.errorMessage = 'No se pudieron cargar los proyectos. Verifique su conexión.';
        }
      }
    });
  }

  public get filteredProyectos(): Proyecto[] {
    if (!this.searchTerm) {
      return this.proyectos;
    }
    const term = this.searchTerm.toLowerCase();
    return this.proyectos.filter(p =>
      p.nombre.toLowerCase().includes(term) ||
      p.codigo.toLowerCase().includes(term) ||
      (p.descripcion && p.descripcion.toLowerCase().includes(term)) ||
      (p.propietario && p.propietario.username.toLowerCase().includes(term))
    );
  }

  public onSearchChange(term: string): void {
    this.searchTerm = term;
  }

  public onClearSearch(): void {
    this.searchTerm = '';
  }

  public openCreateModal(): void {
    this.isModalOpen = true;
  }

  public onModalClose(): void {
    this.isModalOpen = false;
  }

  public onProjectCreated(nuevoProyecto: Proyecto): void {
    this.proyectos = [nuevoProyecto, ...this.proyectos];
    this.isModalOpen = false;
  }

  public openDeleteModal(proyecto: Proyecto): void {
    this.projectToDelete = proyecto;
    this.isDeleteModalOpen = true;
  }

  public onDeleteModalClose(): void {
    this.isDeleteModalOpen = false;
    this.projectToDelete = null;
  }

  public onProjectDeleted(deletedId: number): void {
    const nombre = this.projectToDelete?.nombre || 'El proyecto';
    this.proyectos = this.proyectos.filter(p => p.id !== deletedId);
    this.isDeleteModalOpen = false;
    this.projectToDelete = null;
    this.toastService.exito(`${nombre} ha sido eliminado exitosamente.`);
  }
}
