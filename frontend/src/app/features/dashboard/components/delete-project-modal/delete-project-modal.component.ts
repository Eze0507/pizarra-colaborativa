import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ProjectsService } from '../../services/projects.service';
import { Proyecto } from '../../interfaces/proyecto.interface';
import { CustomButtonComponent } from '../../../../shared/components/custom-button/custom-button.component';

@Component({
  selector: 'app-delete-project-modal',
  standalone: true,
  imports: [CommonModule, CustomButtonComponent],
  templateUrl: './delete-project-modal.component.html',
  styleUrls: ['./delete-project-modal.component.css']
})
export class DeleteProjectModalComponent {
  @Input() public isOpen = false;
  @Input() public proyecto: Proyecto | null = null;
  @Output() public readonly closed = new EventEmitter<void>();
  @Output() public readonly projectDeleted = new EventEmitter<number>();

  private readonly projectsService = inject(ProjectsService);

  public isDeleting = false;
  public errorMessage: string | null = null;

  public close(): void {
    if (this.isDeleting) return;
    this.errorMessage = null;
    this.closed.emit();
  }

  public confirmDelete(): void {
    if (!this.proyecto || this.isDeleting) return;

    this.isDeleting = true;
    this.errorMessage = null;

    const proyectoId = this.proyecto.id;

    this.projectsService.eliminarProyecto(proyectoId).subscribe({
      next: () => {
        this.isDeleting = false;
        this.projectDeleted.emit(proyectoId);
      },
      error: (error: HttpErrorResponse) => {
        this.isDeleting = false;
        if (error.error && typeof error.error.detail === 'string') {
          this.errorMessage = error.error.detail;
        } else {
          this.errorMessage = 'No se pudo eliminar el proyecto. Verifique sus permisos e intente nuevamente.';
        }
      }
    });
  }
}
