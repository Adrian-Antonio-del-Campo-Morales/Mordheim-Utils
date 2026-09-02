# Modificar la aplicación

1. Modele el caso de uso en `application/` sin Tkinter.
2. Reutilice `mordheim_construction` para legalidad y `combat.vectorized` para análisis.
3. Devuelva tipos explícitos y acepte cancelación/progreso para trabajos largos.
4. Mantenga en `ui/` el hilo, `after` y la presentación.
5. Versione cambios persistidos sin romper la lectura de workbooks existentes.

Terminado cuando se prueba sin ventana y los round-trips persistidos siguen pasando.
