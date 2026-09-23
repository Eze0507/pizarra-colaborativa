import { UserSimple } from './proyecto.interface';

export interface ProyectoInvitacionResumen {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  propietario: UserSimple;
}

export interface InvitacionPendiente {
  id: number;
  proyecto: ProyectoInvitacionResumen;
  rol: 'propietario' | 'editor' | 'visualizador';
  estado: 'pendiente' | 'activo';
  fecha_ingreso: string;
}

export interface RespuestaAceptarInvitacion {
  detail: string;
  proyecto: {
    id: number;
    codigo: string;
    nombre: string;
  };
  colaborador: {
    id: number;
    username: string;
    rol: string;
    estado: string;
  };
}

export interface RespuestaRechazarInvitacion {
  detail: string;
}
