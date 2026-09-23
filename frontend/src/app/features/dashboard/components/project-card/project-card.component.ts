import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Proyecto } from '../../interfaces/proyecto.interface';
import { TokenStorageService } from '../../../../core/services/token-storage.service';

@Component({
  selector: 'app-project-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './project-card.component.html',
  styleUrls: ['./project-card.component.css']
})
export class ProjectCardComponent {
  @Input({ required: true }) public proyecto!: Proyecto;
  @Output() public readonly delete = new EventEmitter<Proyecto>();

  private readonly router = inject(Router);
  private readonly tokenStorage = inject(TokenStorageService);

  public get isOwner(): boolean {
    if (this.proyecto.es_propietario !== undefined) {
      return this.proyecto.es_propietario;
    }
    const currentUser = this.tokenStorage.getUser();
    if (!currentUser || !this.proyecto.propietario) return false;
    return this.proyecto.propietario.id === currentUser.id || this.proyecto.propietario.username === currentUser.username;
  }

  public get formattedDate(): string {
    if (!this.proyecto.fecha_actualizacion) return '';
    try {
      const date = new Date(this.proyecto.fecha_actualizacion);
      return new Intl.DateTimeFormat('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    } catch {
      return this.proyecto.fecha_actualizacion;
    }
  }

  public openProject(): void {
    this.router.navigate(['/pizarra', this.proyecto.id]);
  }

  public onDeleteProject(event: MouseEvent): void {
    event.stopPropagation();
    this.delete.emit(this.proyecto);
  }
}
