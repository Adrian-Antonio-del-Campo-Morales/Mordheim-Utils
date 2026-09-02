# Implementar comportamiento de combate

1. Clasifique el efecto como construcción, modificador, resolución local o flujo con estado.
2. Use `construction`, `domain.effects`, `combat.phases` o `combat/modular` respectivamente.
3. Comparta el preparador de contexto entre orquestador y verificador.
4. Inyecte `DiceSource` y `DecisionPolicy`; no consulte azar global ni la UI.
5. Añada tests de fase o la mini-secuencia mínima.

Ejemplo: regeneración bloqueada por fuego se compila como dato y la consumen el contexto y la fase de salvación especial.

Terminado cuando el binding llega a un resultado observable y pasan activación, ausencia, límites y arquitectura.
