import { AtributoDiagrama, EntidadDiagrama, MapasIdsSnapshot, OperacionDiagrama, RelacionDiagrama, VisibilidadUML } from '../interfaces/diagrama.interface';

const SIMBOLO: Record<VisibilidadUML, string> = { public: '+', protected: '#', private: '-', package: '~' };
export function nombreTipo(tipo: string, ref: number | null | undefined, entidades: ReadonlyMap<number, EntidadDiagrama>): string {
  return ref == null ? (tipo || 'string') : (entidades.get(ref)?.nombre || `«no resuelto:${ref}»`);
}
export function etiquetaAtributo(a: AtributoDiagrama, entidades: ReadonlyMap<number, EntidadDiagrama>): string {
  const valor = a.valor_predeterminado ? ` = ${a.valor_predeterminado}` : '';
  const texto = `${a.es_clave ? '[PK] ' : ''}${SIMBOLO[a.visibilidad || 'private']} ${a.nombre} : ${nombreTipo(a.tipo, a.tipo_referencia_id, entidades)}${valor}`;
  return a.es_estatico ? [...texto].map(c => `${c}\u0332`).join('') : texto;
}
export function etiquetaOperacion(o: OperacionDiagrama, entidades: ReadonlyMap<number, EntidadDiagrama>): string {
  const params = [...(o.parametros || [])].sort((a,b) => a.orden-b.orden)
    .map(p => `${p.nombre}: ${nombreTipo(p.tipo, p.tipo_referencia_id, entidades)}`).join(', ');
  const texto = `${SIMBOLO[o.visibilidad || 'public']} ${o.nombre}(${params}) : ${nombreTipo(o.tipo_retorno || 'void', o.retorno_referencia_id, entidades)}`;
  return o.es_estatico ? [...texto].map(c => `${c}\u0332`).join('') : texto;
}
const remap = (id: number | null | undefined, mapa?: Record<string, number>) => id == null || !mapa ? id : (mapa[String(id)] ?? id);
export function aplicarMapasIds(entidades: EntidadDiagrama[], relaciones: RelacionDiagrama[], mapas: MapasIdsSnapshot) {
  return {
    entidades: entidades.map(e => ({ ...e, id: remap(e.id,mapas.id_map) as number,
      atributos: (e.atributos||[]).map(a => ({...a,id:remap(a.id,mapas.attr_id_map) as number,tipo_referencia_id:remap(a.tipo_referencia_id,mapas.id_map)})),
      operaciones: (e.operaciones||[]).map(o => ({...o,id:remap(o.id,mapas.operation_id_map) as number,retorno_referencia_id:remap(o.retorno_referencia_id,mapas.id_map),
        parametros:(o.parametros||[]).map(p=>({...p,id:remap(p.id,mapas.parameter_id_map) as number,tipo_referencia_id:remap(p.tipo_referencia_id,mapas.id_map)}))})) })),
    relaciones: relaciones.map(r => ({...r,id:remap(r.id,mapas.rel_id_map) as number,entidad_origen_id:remap(r.entidad_origen_id,mapas.id_map) as number,
      entidad_destino_id:remap(r.entidad_destino_id,mapas.id_map) as number,clase_asociacion_id:remap(r.clase_asociacion_id,mapas.id_map)}))
  };
}
