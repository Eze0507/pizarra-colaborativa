import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Proyecto } from '../../interfaces/proyecto.interface';

@Component({
  selector: 'app-project-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './project-card.component.html',
  styleUrls: ['./project-card.component.css']
})
export class ProjectCardComponent {
  @Input({ required: true }) public proyecto!: Proyecto;

  private readonly router = inject(Router);

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
    this.router.navigate(['/pizarra']);
  }
}
