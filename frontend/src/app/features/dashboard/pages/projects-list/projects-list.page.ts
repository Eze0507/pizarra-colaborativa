import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ProjectsService } from '../../services/projects.service';
import { Proyecto } from '../../interfaces/proyecto.interface';
import { ProjectCardComponent } from '../../components/project-card/project-card.component';
import { CreateProjectModalComponent } from '../../components/create-project-modal/create-project-modal.component';

@Component({
  selector: 'app-projects-list-page',
  standalone: true,
  imports: [CommonModule, ProjectCardComponent, CreateProjectModalComponent],
  templateUrl: './projects-list.page.html',
  styleUrls: ['./projects-list.page.css']
})
export class ProjectsListPage implements OnInit {
  private readonly projectsService = inject(ProjectsService);

  public proyectos: Proyecto[] = [];
  public isLoading = true;
  public errorMessage: string | null = null;
  public isModalOpen = false;

  public ngOnInit(): void {
    this.loadProyectos();
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
}
