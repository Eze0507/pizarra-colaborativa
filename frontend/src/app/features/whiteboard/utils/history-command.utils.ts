export interface HistoryCommand {
  action: 'undo' | 'redo' | 'restore';
  kind?: 'any' | 'entity' | 'attribute' | 'method' | 'relationship';
  name?: string;
  owner?: string;
  endpoints?: string[];
  latest?: boolean;
  operation_id?: string;
}
export type ParsedHistoryCommand = HistoryCommand | { action: 'clarify'; message: string } | null;

export function normalizeHistoryText(value: string): string {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

/** Gramática anclada a la instrucción completa; conserva los nombres originales. */
export function parseHistoryCommand(text: string): ParsedHistoryCommand {
  const original = text.trim().replace(/^[¡¿\s]+|[.,!?;:\s]+$/g, '').replace(/\s+/g, ' ');
  const normalized = normalizeHistoryText(original);
  const clarify = { action: 'clarify' as const, message: 'Indica una sola acción de historial y el elemento que deseas recuperar.' };
  const historyVerb = /^(?:deshacer|deshaz|revertir|revierte|rehacer|rehaz|volver atras|restaura(?:r)?|recupera(?:r)?)\b/;
  // Una orden compuesta que contiene historial nunca se envía parcialmente al proveedor.
  if (/(?:\by\b|[;.?!]|\bluego\b|\bdespues\b).*(?:\bdeshaz\b|\bdeshacer\b|\brevierte\b|\brevertir\b|\brehacer\b|\brestaura(?:r)?\b|\brecupera(?:r)?\b)/.test(normalized)) return clarify;
  if (!historyVerb.test(normalized)) return null;
  if (/^(?:deshacer|deshaz)(?: (?:el )?ultimo cambio)?$|^volver atras$/.test(normalized)) return { action: 'undo' };
  if (/^(?:revertir|revierte)(?: (?:el |los )?(?:ultimo )?cambios?)?$/.test(normalized)) return { action: 'undo' };
  if (/^(?:rehacer|rehaz)(?: (?:el )?ultimo cambio)?$/.test(normalized)) return { action: 'redo' };
  const prefix = /^(?:(?:restaura(?:r)?|recupera(?:r)?)\s+|deshaz (?:la )?eliminacion de\s+)/.exec(normalized);
  if (!prefix) return clarify;
  const target = original.slice(prefix[0].length);
  const n = normalizeHistoryText(target);
  if (/;|\b(?:despues|luego|crea|agrega|elimina|borra|anade|renombra|mueve)\b/.test(n)) return clarify;
  const types: Record<string, HistoryCommand['kind']> = { clase: 'entity', entidad: 'entity', atributo: 'attribute', metodo: 'method', operacion: 'method', relacion: 'relationship' };
  const last = /^(?:(?:el|la) )?ultim[oa] (clase|entidad|atributo|metodo|operacion|relacion) eliminad[oa]$/.exec(n);
  if (last) return { action: 'restore', kind: types[last[1]], latest: true };
  const relationship = /^(?:la )?relacion entre (.+) y (.+)$/.exec(n);
  if (relationship) {
    const start = n.indexOf('entre ') + 6;
    const split = n.indexOf(' y ', start);
    return { action: 'restore', kind: 'relationship', endpoints: [target.slice(start, split), target.slice(split + 3)] };
  }
  if (/\by\b/.test(n)) return clarify;
  const typed = /^(?:(?:el|la) )?(clase|entidad|atributo|metodo|operacion|relacion)\s+/.exec(n);
  const nameWithOwner = target.slice(typed?.[0].length || 0).replace(/^["'“]|["'”]$/g, '');
  if (!nameWithOwner) return clarify;
  const ownerMatch = /\s+de\s+(?:(?:la )?(?:clase|entidad)\s+)?/i.exec(normalizeHistoryText(nameWithOwner));
  const kind = typed ? types[typed[1]] : n === 'la asociacion' || n === 'asociacion' ? 'relationship' : 'any';
  return { action: 'restore', kind,
    name: ownerMatch ? nameWithOwner.slice(0, ownerMatch.index) : nameWithOwner.replace(/^la asociaci[oó]n$/i, 'asociacion'),
    ...(ownerMatch ? { owner: nameWithOwner.slice(ownerMatch.index + ownerMatch[0].length) } : {}) };
}

export function historyShortcut(event: KeyboardEvent, modalOpen: boolean): 'undo' | 'redo' | null {
  if (modalOpen || event.altKey || event.repeat || !(event.ctrlKey || event.metaKey)) return null;
  const editable = (target: EventTarget | null): boolean => target instanceof HTMLElement &&
    (!!target.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"]), [role="textbox"]') || target.isContentEditable);
  if (editable(event.target) || editable(document.activeElement)) return null;
  const key = event.key.toLowerCase();
  if (key === 'z') return event.shiftKey ? 'redo' : 'undo';
  if (key === 'y' && event.ctrlKey && !event.shiftKey) return 'redo';
  return null;
}
