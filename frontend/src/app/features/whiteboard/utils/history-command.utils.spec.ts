import { historyShortcut, parseHistoryCommand } from './history-command.utils';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { AsistenteIaService } from '../services/asistente-ia.service';

describe('Parser determinista de historial', () => {
  for (const text of ['revierte', 'Revertir', 'revierte los cambios', 'revertir el último cambio']) {
    it(`reconoce revertir como Undo completo: ${text}`, () => expect(parseHistoryCommand(text)).toEqual({ action: 'undo' }));
  }
  for (const text of ['deshacer', 'Deshaz.', ' DESHAZ el último cambio! ', 'volver atrás']) {
    it(`reconoce Undo completo: ${text}`, () => expect(parseHistoryCommand(text)).toEqual({ action: 'undo' }));
  }
  for (const text of ['rehacer', 'Rehaz', 'rehaz el último cambio']) {
    it(`reconoce Redo completo: ${text}`, () => expect(parseHistoryCommand(text)).toEqual({ action: 'redo' }));
  }
  for (const verb of ['Restaura', 'Restaurar', 'Recupera', 'Recuperar']) {
    it(`conserva nombres y tildes: ${verb}`, () => {
      expect(parseHistoryCommand(`${verb} el atributo Dirección de Unidad.`)).toEqual({ action: 'restore', kind: 'attribute', name: 'Dirección', owner: 'Unidad' });
    });
  }
  it('reconoce clases, métodos, último eliminado y relaciones', () => {
    expect(parseHistoryCommand('Restaura la clase unidad')).toEqual({ action: 'restore', kind: 'entity', name: 'unidad' });
    expect(parseHistoryCommand('Restaura el método guardar de unidad')).toEqual({ action: 'restore', kind: 'method', name: 'guardar', owner: 'unidad' });
    expect(parseHistoryCommand('Recupera la última clase eliminada')).toEqual({ action: 'restore', kind: 'entity', latest: true });
    expect(parseHistoryCommand('Restaura la relación entre Unidad y Producto')).toEqual({ action: 'restore', kind: 'relationship', endpoints: ['Unidad', 'Producto'] });
    expect(parseHistoryCommand('Deshaz la eliminación de dirección')).toEqual({ action: 'restore', kind: 'any', name: 'dirección' });
  });
  for (const text of ['Crea una clase llamada Restaurar', 'Agrega dirección a unidad', 'Elimina dirección de unidad']) {
    it(`conserva el flujo normal: ${text}`, () => expect(parseHistoryCommand(text)).toBeNull());
  }
  for (const text of ['Deshaz y después crea cliente', 'Restaura unidad y crea cliente', 'Crea cliente y deshaz', 'Restaurar', 'Deshacer dos cambios', 'Recupera unidad; crea producto']) {
    it(`no ejecuta partes ambiguas: ${text}`, () => expect(parseHistoryCommand(text)?.action).toBe('clarify'));
  }
});

describe('Atajos de historial', () => {
  it('reconoce Ctrl/Cmd y sus variantes', () => {
    for (const modifier of ['ctrlKey', 'metaKey']) {
      expect(historyShortcut(new KeyboardEvent('keydown', { key: 'z', [modifier]: true }), false)).toBe('undo');
      expect(historyShortcut(new KeyboardEvent('keydown', { key: 'Z', shiftKey: true, [modifier]: true }), false)).toBe('redo');
    }
    expect(historyShortcut(new KeyboardEvent('keydown', { key: 'y', ctrlKey: true }), false)).toBe('redo');
  });
  for (const tag of ['input', 'textarea', 'select', 'div']) {
    it(`no intercepta edición en ${tag}`, () => {
      const input = document.createElement(tag);
      if (tag === 'div') input.contentEditable = 'true';
      document.body.appendChild(input);
      input.focus();
      expect(historyShortcut(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true }), false)).toBeNull();
      input.remove();
    });
  }
  it('no intercepta modales ni repeticiones de tecla', () => {
    expect(historyShortcut(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true }), true)).toBeNull();
    expect(historyShortcut(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, repeat: true }), false)).toBeNull();
  });
});

describe('Contexto de relaciones para la IA', () => {
  let service: AsistenteIaService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [AsistenteIaService, provideHttpClient()] });
    service = TestBed.inject(AsistenteIaService);
  });

  it('incluye ambas cardinalidades y conserva los valores vacios', () => {
    const contexto = service.extraerContextoDiagrama([], [
      { id: 8, entidad_origen_id: 1, entidad_destino_id: 2, tipo: 'asociacion', cardinalidad_origen: '1', cardinalidad_destino: '0..*' } as any,
      { id: 9, entidad_origen_id: 2, entidad_destino_id: 3, tipo: 'asociacion' } as any
    ]);

    expect(contexto.relaciones[0].cardinalidad_origen).toBe('1');
    expect(contexto.relaciones[0].cardinalidad_destino).toBe('0..*');
    expect(contexto.relaciones[1].cardinalidad_origen).toBe('');
    expect(contexto.relaciones[1].cardinalidad_destino).toBe('');
  });
});
