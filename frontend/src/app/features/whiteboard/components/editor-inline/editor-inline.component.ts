import {
  Component,
  Input,
  Output,
  EventEmitter,
  ElementRef,
  ViewChild,
  OnChanges,
  SimpleChanges
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { AtributoDiagrama } from '../../interfaces/diagrama.interface';
import {
  PosicionEditor,
  TipoEditor,
  GuardarEditorPayload
} from '../../interfaces/whiteboard-ui.interface';

@Component({
  selector: 'app-editor-inline',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './editor-inline.component.html',
  styleUrls: ['./editor-inline.component.css']
})
export class EditorInlineComponent implements OnChanges {
  @ViewChild('inlineInput', { static: false }) private inlineInputRef?: ElementRef<HTMLInputElement>;

  @Input() public activo = false;
  @Input() public tipo: TipoEditor = 'nombre';
  @Input() public posicion: PosicionEditor = { x: 0, y: 0, w: 0, h: 0 };
  @Input() public valor = '';
  @Input() public placeholder = '';
  @Input() public tiposBackend: AtributoDiagrama['tipo'][] = [
    'string',
    'integer',
    'long',
    'double',
    'boolean',
    'date'
  ];

  @Output() public readonly guardar = new EventEmitter<GuardarEditorPayload>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public editorValor = '';
  public mostrarSugerenciasTipos = false;
  public sugerenciasFiltradas: AtributoDiagrama['tipo'][] = [];
  public indiceSugerenciaSeleccionada = 0;

  private ignorarSiguienteBlur = false;
  private blurTimer: ReturnType<typeof setTimeout> | null = null;

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['valor']) {
      this.editorValor = this.valor || '';
      if (this.inlineInputRef?.nativeElement) {
        this.inlineInputRef.nativeElement.value = this.editorValor;
      }
    }
    if (changes['activo']) {
      if (this.activo) {
        this.editorValor = this.valor || '';
        this.mostrarSugerenciasTipos = false;
        this.ignorarSiguienteBlur = false;
        setTimeout(() => {
          this.focalizarInput();
        });
      } else {
        this.editorValor = '';
        this.mostrarSugerenciasTipos = false;
        this.sugerenciasFiltradas = [];
        if (this.inlineInputRef?.nativeElement) {
          this.inlineInputRef.nativeElement.value = '';
        }
      }
    } else if (changes['tipo']) {
      this.editorValor = this.valor || '';
      this.mostrarSugerenciasTipos = false;
      if (this.inlineInputRef?.nativeElement) {
        this.inlineInputRef.nativeElement.value = this.editorValor;
      }
    }
  }

  private focalizarInput(): void {
    if (!this.inlineInputRef?.nativeElement) return;
    const input = this.inlineInputRef.nativeElement;
    input.value = this.editorValor;
    input.focus();
    const len = input.value.length;
    input.setSelectionRange(len, len);
  }

  public onInput(evt: Event): void {
    const input = evt.target as HTMLInputElement;
    const val = input.value;
    this.editorValor = val;

    if (this.tipo === 'nombre') {
      this.mostrarSugerenciasTipos = false;
      return;
    }

    const indexDosPuntos = val.lastIndexOf(':');
    if (indexDosPuntos !== -1) {
      const queryTipo = val.substring(indexDosPuntos + 1).trim().toLowerCase();
      this.sugerenciasFiltradas = this.tiposBackend.filter(t =>
        t.toLowerCase().startsWith(queryTipo)
      );
      this.mostrarSugerenciasTipos = this.sugerenciasFiltradas.length > 0;
      this.indiceSugerenciaSeleccionada = this.sugerenciasFiltradas.length > 0 ? 0 : -1;
    } else {
      this.mostrarSugerenciasTipos = false;
    }
  }

  public onKeydown(evt: KeyboardEvent): void {
    if (this.mostrarSugerenciasTipos && this.sugerenciasFiltradas.length > 0) {
      if (evt.key === 'ArrowDown') {
        evt.preventDefault();
        this.indiceSugerenciaSeleccionada =
          (this.indiceSugerenciaSeleccionada + 1) % this.sugerenciasFiltradas.length;
        return;
      }

      if (evt.key === 'ArrowUp') {
        evt.preventDefault();
        this.indiceSugerenciaSeleccionada =
          (this.indiceSugerenciaSeleccionada - 1 + this.sugerenciasFiltradas.length) %
          this.sugerenciasFiltradas.length;
        return;
      }

      if (evt.key === 'Tab' || (evt.key === 'Enter' && this.indiceSugerenciaSeleccionada >= 0)) {
        evt.preventDefault();
        const tipoElegido = this.sugerenciasFiltradas[this.indiceSugerenciaSeleccionada];
        this.aplicarTipoAlInput(tipoElegido);
        return;
      }

      if (evt.key === 'Escape') {
        evt.preventDefault();
        this.mostrarSugerenciasTipos = false;
        return;
      }
    }

    if (evt.key === 'Enter') {
      evt.preventDefault();
      this.ignorarSiguienteBlur = true;
      this.emitirGuardado(true);
    } else if (evt.key === 'Escape') {
      evt.preventDefault();
      this.ignorarSiguienteBlur = true;
      this.editorValor = '';
      if (this.inlineInputRef?.nativeElement) {
        this.inlineInputRef.nativeElement.value = '';
      }
      this.cancelar.emit();
    }
  }

  public onSeleccionarTipo(tipo: AtributoDiagrama['tipo'], evt: MouseEvent): void {
    evt.preventDefault();
    this.aplicarTipoAlInput(tipo);
  }

  public aplicarTipoAlInput(tipo: AtributoDiagrama['tipo']): void {
    if (!this.inlineInputRef) return;
    const input = this.inlineInputRef.nativeElement;
    const val = input.value;
    const indexDosPuntos = val.lastIndexOf(':');
    let nuevoTexto = '';

    if (indexDosPuntos !== -1) {
      const prefijo = val.substring(0, indexDosPuntos + 1).trim();
      nuevoTexto = `${prefijo} ${tipo}`;
    } else {
      nuevoTexto = `${val.trim()}: ${tipo}`;
    }

    input.value = nuevoTexto;
    this.editorValor = nuevoTexto;
    this.mostrarSugerenciasTipos = false;
    input.focus();
  }

  public obtenerAbrevTipo(tipo: AtributoDiagrama['tipo']): string {
    switch (tipo) {
      case 'string':  return 'str';
      case 'integer': return 'int';
      case 'long':    return 'long';
      case 'double':  return 'dbl';
      case 'boolean': return 'bool';
      case 'date':    return 'date';
      default:        return tipo;
    }
  }

  public onBlur(): void {
    if (this.ignorarSiguienteBlur) {
      this.ignorarSiguienteBlur = false;
      return;
    }
    if (this.blurTimer) {
      clearTimeout(this.blurTimer);
    }
    this.blurTimer = setTimeout(() => {
      this.emitirGuardado(false);
      this.blurTimer = null;
    }, 120);
  }

  private emitirGuardado(encadenar: boolean): void {
    if (this.blurTimer) {
      clearTimeout(this.blurTimer);
      this.blurTimer = null;
    }
    const inputEl = this.inlineInputRef?.nativeElement;
    const val = inputEl ? inputEl.value.trim() : this.editorValor.trim();
    this.editorValor = '';
    if (inputEl) {
      inputEl.value = '';
    }
    this.guardar.emit({ valor: val, encadenar });
  }
}
