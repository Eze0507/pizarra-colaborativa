import {
  Component,
  OnInit,
  OnDestroy,
  Input,
  Output,
  EventEmitter,
  ElementRef,
  ViewChild,
  OnChanges,
  SimpleChanges,
  inject,
  ChangeDetectorRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { AtributoDiagrama } from '../../interfaces/diagrama.interface';
import {
  PosicionEditor,
  TipoEditor,
  GuardarEditorEvento
} from '../../interfaces/whiteboard-ui.interface';
import { WhiteboardCanvasService } from '../../services/whiteboard-canvas.service';

const TIPOS_BACKEND_DEFECTO: AtributoDiagrama['tipo'][] = [
  'string',
  'integer',
  'long',
  'double',
  'boolean',
  'date'
];

@Component({
  selector: 'app-editor-inline',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './editor-inline.component.html',
  styleUrls: ['./editor-inline.component.css']
})
export class EditorInlineComponent implements OnInit, OnDestroy, OnChanges {
  @ViewChild('inlineInput', { static: false }) private inlineInputRef?: ElementRef<HTMLInputElement>;

  private readonly canvasService = inject(WhiteboardCanvasService, { optional: true });
  private readonly cdr           = inject(ChangeDetectorRef);
  private sub: Subscription | null = null;

  @Input() public activo = false;
  @Input() public tipo: TipoEditor = 'nombre';
  @Input() public posicion: PosicionEditor = { x: 0, y: 0, w: 0, h: 0 };
  @Input() public valor = '';
  @Input() public placeholder = '';
  @Input() public tiposBackend: AtributoDiagrama['tipo'][] = TIPOS_BACKEND_DEFECTO;

  @Output() public readonly guardar = new EventEmitter<GuardarEditorEvento>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public editorValor = '';
  public mostrarSugerenciasTipos = false;
  public sugerenciasFiltradas: AtributoDiagrama['tipo'][] = [];
  public indiceSugerenciaSeleccionada = 0;

  private entidadId: number | null = null;
  private atributoIndex: number | null = null;
  private relacionId: number | null = null;

  private ignorarSiguienteBlur = false;
  private blurTimer: ReturnType<typeof setTimeout> | null = null;

  public ngOnInit(): void {
    if (!this.canvasService) return;

    this.sub = new Subscription();

    // 1. Solicitud de edición del nombre de entidad
    this.sub.add(
      this.canvasService.solicitudEditorNombre$.subscribe(entidadId => {
        const pos = this.canvasService!.obtenerPosicionEditorNombre(entidadId);
        const entidad = this.canvasService!.getEntidad(entidadId);
        if (!pos || !entidad) return;

        this.relacionId = null;
        this.entidadId = entidadId;
        this.tipo = 'nombre';
        this.atributoIndex = null;
        this.valor = entidad.nombre || '';
        this.editorValor = this.valor;
        this.placeholder = 'Escribir nombre de entidad...';
        this.posicion = pos;
        this.activo = true;
        this.cdr.detectChanges();
        setTimeout(() => this.focalizarInput());
      })
    );

    // 2. Solicitud de creación de nuevo atributo
    this.sub.add(
      this.canvasService.solicitudEditorNuevoAtributo$.subscribe(entidadId => {
        const pos = this.canvasService!.obtenerPosicionEditorNuevoAtributo(entidadId);
        if (!pos) return;

        this.relacionId = null;
        this.entidadId = entidadId;
        this.tipo = 'nuevo_atributo';
        this.atributoIndex = null;
        this.valor = '';
        this.editorValor = '';
        this.placeholder = 'Ej: - id: integer [pk] o - nombre: string';
        this.posicion = pos;
        this.activo = true;
        this.cdr.detectChanges();
        setTimeout(() => this.focalizarInput());
      })
    );

    // 3. Solicitud de edición de atributo existente
    this.sub.add(
      this.canvasService.solicitudEditorAtributo$.subscribe(ev => {
        const pos = this.canvasService!.obtenerPosicionEditorAtributo(ev.entidadId, ev.index);
        const entidad = this.canvasService!.getEntidad(ev.entidadId);
        if (!pos || !entidad?.atributos?.[ev.index]) return;

        const attr = entidad.atributos[ev.index];
        this.relacionId = null;
        this.entidadId = ev.entidadId;
        this.tipo = 'editar_atributo';
        this.atributoIndex = ev.index;

        const pkStr = attr.es_clave ? '[pk] ' : '';
        const optStr = attr.es_nulo ? '?' : '';
        const nombreLimpio = attr.nombre.replace(/^[-+~#]\s*/, '').trim();
        this.valor = `${pkStr}- ${nombreLimpio}: ${attr.tipo}${optStr}`;
        this.editorValor = this.valor;
        this.placeholder = 'Ej: - nombre: string (vacío para eliminar)';
        this.posicion = pos;
        this.activo = true;
        this.cdr.detectChanges();
        setTimeout(() => this.focalizarInput());
      })
    );

    // 4. Solicitud de edición de etiqueta/nombre de relación
    this.sub.add(
      this.canvasService.solicitudEditorNombreRelacion$.subscribe(ev => {
        const relacion = this.canvasService!.getRelacion(ev.relacionId);
        if (!relacion) return;

        this.entidadId = null;
        this.atributoIndex = null;
        this.relacionId = ev.relacionId;
        this.tipo = 'nombre_relacion';
        this.valor = relacion.nombre_relacion || '';
        this.editorValor = this.valor;
        this.placeholder = 'nombre_relacion';
        this.posicion = ev.pos;
        this.activo = true;
        this.cdr.detectChanges();
        setTimeout(() => this.focalizarInput());
      })
    );

    // 5. Cierre general de modales
    this.sub.add(
      this.canvasService.cerrarModales$.subscribe(() => {
        if (this.activo) {
          this.activo = false;
          this.cdr.detectChanges();
        }
      })
    );
  }

  public ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

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
      this.activo = false;
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
    this.activo = false;
    this.guardar.emit({
      tipo: this.tipo,
      valor: val,
      encadenar,
      entidadId: this.entidadId,
      atributoIndex: this.atributoIndex,
      relacionId: this.relacionId
    });
  }
}
