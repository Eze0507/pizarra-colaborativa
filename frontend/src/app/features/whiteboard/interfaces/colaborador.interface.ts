export interface UsuarioBusqueda {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface ColaboradorProyecto {
  id: number;
  usuario: UsuarioBusqueda;
  rol: 'propietario' | 'editor' | 'visualizador';
  estado: 'pendiente' | 'activo';
  fecha_ingreso: string;
}

export interface RespuestaAccionColaborador {
  detail: string;
  colaborador?: ColaboradorProyecto;
}
