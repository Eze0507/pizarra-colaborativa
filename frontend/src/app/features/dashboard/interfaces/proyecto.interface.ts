export interface UserSimple {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface ColaboradorDetalle {
  id: number;
  usuario: UserSimple;
  rol: 'propietario' | 'editor' | 'visualizador';
  estado: 'pendiente' | 'activo';
  fecha_ingreso: string;
}

export interface Proyecto {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  paquete_base: string;
  fecha_creacion: string;
  fecha_actualizacion: string;
  propietario: UserSimple;
  colaboradores_detalle: ColaboradorDetalle[];
}

export interface ProyectoCreateRequest {
  nombre: string;
  descripcion?: string;
}
