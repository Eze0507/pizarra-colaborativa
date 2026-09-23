import { Injectable } from '@angular/core';
import { AtributoDiagrama } from '../interfaces/diagrama.interface';

@Injectable({
  providedIn: 'root'
})
export class DiagramaParserService {
  /**
   * Parsea de forma inteligente el texto ingresado por el usuario para extraer nombre, tipo, PK y nulidad.
   */
  public parsearAtributoTexto(input: string, orden: number, id: number): AtributoDiagrama {
    let limpio = input.trim();
    let esClave = false;
    let esNulo = false;

    // 1. Detectar corchetes [pk] o [PK]
    if (/\[\s*pk\s*\]/i.test(limpio)) {
      esClave = true;
      limpio = limpio.replace(/\[\s*pk\s*\]/gi, '').trim();
    }

    // 2. Detectar palabra clave 'pk' independiente
    if (/\bpk\b/i.test(limpio)) {
      esClave = true;
      limpio = limpio.replace(/\bpk\b/gi, '').trim();
    }

    // 3. Limpiar corchetes vacíos residuales
    limpio = limpio.replace(/\[\s*\]/g, '').trim();

    // 4. Limpiar prefijo de visibilidad UML (+, -, #, ~) al inicio
    limpio = limpio.replace(/^[-+~#]\s*/, '').trim();

    // 5. Detectar nulabilidad
    if (limpio.endsWith('?') || /\bnull\b/i.test(limpio)) {
      esNulo = true;
      limpio = limpio.replace(/\?|\bnull\b/gi, '').trim();
    }

    let nombre = limpio;
    let tipoStr = '';

    if (limpio.includes(':')) {
      const partes = limpio.split(':');
      nombre = partes[0].trim();
      tipoStr = partes[1]?.trim().toLowerCase() || '';
    } else {
      const partes = limpio.split(/\s+/);
      if (partes.length >= 2) {
        nombre = partes[0].trim();
        tipoStr = partes[1].trim().toLowerCase();
      } else {
        nombre = partes[0].trim();
      }
    }

    nombre = nombre.replace(/^[-+~#]\s*/, '').replace(/\[\s*\]/g, '').trim();

    if (nombre.toLowerCase() === 'id' || nombre.toLowerCase().endsWith('_id')) {
      if (!esClave && nombre.toLowerCase() === 'id') esClave = true;
      if (!tipoStr) tipoStr = 'integer';
    }

    const tiposValidos: AtributoDiagrama['tipo'][] = ['string', 'integer', 'long', 'double', 'boolean', 'date'];
    let tipoFinal: AtributoDiagrama['tipo'] = 'string';

    if (tiposValidos.includes(tipoStr as AtributoDiagrama['tipo'])) {
      tipoFinal = tipoStr as AtributoDiagrama['tipo'];
    } else if (tipoStr.startsWith('int')) {
      tipoFinal = 'integer';
    } else if (tipoStr.startsWith('str') || tipoStr.startsWith('var') || tipoStr.startsWith('txt') || tipoStr.startsWith('text')) {
      tipoFinal = 'string';
    } else if (tipoStr.startsWith('bool')) {
      tipoFinal = 'boolean';
    } else if (tipoStr.startsWith('date') || tipoStr.startsWith('time')) {
      tipoFinal = 'date';
    } else if (tipoStr.startsWith('float') || tipoStr.startsWith('dec') || tipoStr.startsWith('num') || tipoStr.startsWith('doub')) {
      tipoFinal = 'double';
    }

    return {
      id,
      nombre: nombre || 'campo',
      tipo: tipoFinal,
      es_clave: esClave,
      es_nulo: esNulo,
      orden
    };
  }
}
