import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ProjectsService } from '../../services/projects.service';
import { Proyecto, ProyectoCreateRequest } from '../../interfaces/proyecto.interface';

@Component({
  selector: 'app-create-project-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './create-project-modal.component.html',
  styleUrls: ['./create-project-modal.component.css']
})
export class CreateProjectModalComponent {
  @Input() public isOpen = false;
  @Output() public readonly closed = new EventEmitter<void>();
  @Output() public readonly projectCreated = new EventEmitter<Proyecto>();

  private readonly fb = inject(FormBuilder);
  private readonly projectsService = inject(ProjectsService);

  public projectForm: FormGroup = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(3)]],
    descripcion: ['']
  });

  public isSubmitting = false;
  public errorMessage: string | null = null;

  public isFieldInvalid(fieldName: string): boolean {
    const field = this.projectForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  public onSubmit(): void {
    if (this.projectForm.invalid) {
      this.projectForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = null;

    const data: ProyectoCreateRequest = {
      nombre: this.projectForm.value.nombre.trim(),
      descripcion: this.projectForm.value.descripcion ? this.projectForm.value.descripcion.trim() : ''
    };

    this.projectsService.crearProyecto(data).subscribe({
      next: (nuevoProyecto: Proyecto) => {
        this.isSubmitting = false;
        this.projectForm.reset();
        this.projectCreated.emit(nuevoProyecto);
      },
      error: (error: HttpErrorResponse) => {
        this.isSubmitting = false;
        if (error.error && typeof error.error.detail === 'string') {
          this.errorMessage = error.error.detail;
        } else if (error.error && typeof error.error.nombre === 'object') {
          this.errorMessage = error.error.nombre[0];
        } else {
          this.errorMessage = 'No se pudo crear el proyecto. Intente nuevamente.';
        }
      }
    });
  }

  public close(): void {
    if (this.isSubmitting) return;
    this.projectForm.reset();
    this.errorMessage = null;
    this.closed.emit();
  }
}
