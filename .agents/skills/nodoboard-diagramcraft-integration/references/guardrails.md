# Checklist de corte seguro

- [ ] Requisito y tarea Fxx/Bxx/Uxx exactos, alcance aprobado por usuario.
- [ ] Se inspeccionaron HEAD/status y cambios preexistentes, incluido `frontend/package-lock.json`.
- [ ] Rama/worktree solo bajo autorización; informes y archivos no rastreados preservados.
- [ ] Roles/membresía del proyecto revalidados en backend por operación, no solo handshake.
- [ ] No hay nueva ruta para escritura sin permisos uniformes.
- [ ] Un cambio de diagrama no puede aplicar snapshot obsoleto sin conflicto/resolución explícita.
- [ ] Semántica ORM y serialización visual preservadas; no crear tercera autoridad de diagrama.
- [ ] Eventos WS aislados por proyecto, actor y permisos; reconexión/duplicados controlados.
- [ ] Operación IA validada en servidor; plan confirmable y ligado a usuario/proyecto/revisión cuando corresponda.
- [ ] No se importaron fallos documentados del donante.
- [ ] Pruebas negativas, positivas y de regresión con datos aislados; sin IA externa por defecto.
- [ ] No migraciones/despliegues/AWS/secrets sin aprobación.
- [ ] Resultado con diff, comandos, tests, limitaciones y estado Git final.
