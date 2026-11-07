import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ModalGeneracionSpringComponent } from './modal-generacion-spring.component';


describe('ModalGeneracionSpringComponent', () => {
  let fixture: ComponentFixture<ModalGeneracionSpringComponent>;
  let component: ModalGeneracionSpringComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [ModalGeneracionSpringComponent] }).compileComponents();
    fixture = TestBed.createComponent(ModalGeneracionSpringComponent);
    component = fixture.componentInstance;
    component.visible = true;
    component.puedeGenerar = true;
    component.ngOnChanges({
      visible: { currentValue: true, previousValue: false, firstChange: true, isFirstChange: () => true }
    });
    fixture.detectChanges();
  });

  it('inicia solo con modelo y valida nombre y paquete', () => {
    expect(component.opciones).toEqual({
      modelo: true, repositorio: false, servicio: false, controlador: false
    });
    expect(component.formularioValido).toBeFalse();
    component.nombreProyecto = 'tienda';
    component.paqueteBase = 'com.ejemplo.tienda';
    expect(component.formularioValido).toBeTrue();
    component.paqueteBase = 'com.class.tienda';
    expect(component.formularioValido).toBeFalse();
  });

  it('activa requisitos y desactiva dependientes de forma visible', () => {
    component.cambiarOpcion('controlador', true);
    expect(component.opciones).toEqual({
      modelo: true, repositorio: true, servicio: true, controlador: true
    });
    expect(component.mensajeOpciones).toContain('requeridas');
    component.cambiarOpcion('repositorio', false);
    expect(component.opciones.servicio).toBeFalse();
    expect(component.opciones.controlador).toBeFalse();
    expect(component.mensajeOpciones).toContain('dependían');
  });

  it('emite una copia coherente y bloquea duplicados', () => {
    component.nombreProyecto = 'tienda';
    component.paqueteBase = 'com.ejemplo.tienda';
    spyOn(component.generar, 'emit');
    component.enviar();
    expect(component.generar.emit).toHaveBeenCalledWith(jasmine.objectContaining({
      nombre_proyecto: 'tienda', paquete_base: 'com.ejemplo.tienda'
    }));
    component.generando = true;
    component.enviar();
    expect(component.generar.emit).toHaveBeenCalledTimes(1);
  });

  it('normaliza nombres escritos manualmente al perder el foco', () => {
    component.nombreProyecto = 'F\u00edsica III';
    component.normalizarNombreProyecto();
    expect(component.nombreProyecto).toBe('fisica-iii');
  });

  it('muestra bloqueo y accion de guardado cuando corresponde', () => {
    component.puedeGenerar = false;
    component.puedeGuardar = true;
    component.motivoBloqueo = 'Guarda el diagrama.';
    fixture.detectChanges();
    const button = fixture.nativeElement.querySelector('.blocked button') as HTMLButtonElement;
    expect(button).not.toBeNull();
    spyOn(component.guardar, 'emit');
    button.click();
    expect(component.guardar.emit).toHaveBeenCalled();
  });
});
