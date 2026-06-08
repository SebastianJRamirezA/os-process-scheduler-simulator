# Simulador de Planificación de Procesos CPU (Multi-Política)

---

## Introducción

El presente informe describe el desarrollo e implementación de un simulador de planificación de CPU multi-política de grado de producción. La gestión del procesador es uno de los componentes más críticos dentro del núcleo de un sistema operativo, ya que determina la eficiencia general del hardware, la latencia de respuesta y la equidad en el reparto de recursos entre las tareas concurrentes.

El objetivo principal de este software es modelar, analizar y visualizar dinámicamente el comportamiento de diversos algoritmos de despacho de hilos de ejecución, abarcando variantes tanto no expulsivas (*non-preemptive*) como expulsivas (*preemptive*). A través de una carga de trabajo estocástica basada en un modelo de simulación discreta por ticks de reloj, la herramienta permite contrastar de manera empírica el impacto de cada política sobre la utilización de la CPU y los tiempos de tránsito de los procesos en el sistema.

---

## Decisiones de Diseño

### Selección de Lenguaje e Interfaz Gráfica

Se seleccionó **Python** como lenguaje de programación principal debido a su versatilidad para el prototipado rápido de estructuras lógicas complejas y su robusto ecosistema de bibliotecas analíticas. Para el desarrollo del entorno visual se optó por **Tkinter**, la interfaz gráfica estándar nativa de Python, complementada con los widgets optimizados de **TTK** (*Themed Tkinter*).

### Estructuras de Datos Utilizadas

La fidelidad de la simulación depende de la eficiencia de las estructuras de datos que modelan las micro-colas del sistema operativo:

* **Cola de Listos (`ready_queue`):** Implementada mediante una lista nativa de Python (`list`). Actúa como una estructura de datos flexible que permite operaciones de extracción FIFO (`pop(0)`) para algoritmos clásicos, y reordenamientos internos (*in-place sorting*) basados en criterios de ordenamiento lambda cuando operan algoritmos condicionales como SJF o Prioridades.
* **Conjunto de Bloqueados (`blocked_set`):** Implementado mediante un conjunto mutativo (`set`). Dado que los procesos en estado de Entrada/Salida (E/S) operan de manera independiente y asíncrona respecto al despachador de la CPU, un `set` proporciona un tiempo constante $O(1)$ para la inserción y remoción de bloques de control al finalizar sus ráfagas de E/S de manera desordenada.
* **Matrices de Historial y Telemetría:** Se emplearon arrays lineales (`list`) acotados a un tamaño máximo de 40 ranuras de memoria histórica mediante operaciones de expulsión en cascada (`pop(0)`). Esto funciona como una ventana deslizante que alimenta al vector de señales de Matplotlib.

---

## Arquitectura del Simulador

El software está diseñado bajo un paradigma modular orientado a objetos, distribuyendo las responsabilidades del sistema en componentes autónomos que interactúan de forma desacoplada:

```
[ main.py ] ---> Inicia la aplicación
     |
     v
[ gui.py (SchedulerGUI) ] <--- Interfaz, Gráficos y Bucle de Reloj (.after)
     |
     +---> [ process_generator.py (ProcessGenerator) ] ---> Genera Lote de Procesos
     |
     +---> [ process_scheduler.py (ProcessScheduler) ] ---> Motor de Despacho (Colas)
                 |
                 +---> [ process.py (Process / PCB) ] ---> Máquina de Estados del Proceso

```

### Máquina de Estados del Proceso (PCB)

Cada proceso se comporta como una máquina de estados discreta administrada por la clase `Process`, la cual encapsula los atributos esenciales de un Bloque de Control de Proceso (PCB). Los estados transicionan según la siguiente lógica:

* **READY (Listos):** El proceso espera en la cola de despacho. Incrementa su métrica interna `wait_time` en cada unidad de tiempo.
* **RUNNING (Ejecución):** El proceso posee el token de la CPU. Decrementa su `remaining_time`. Si este llega a cero, transiciona a `TERMINATED` calculando los tiempos de retorno finales.
* **BLOCKED (Bloqueado por E/S):** El proceso ha cedido el control del procesador. Decrementa `remaining_io_time` e incrementa su contador `blocked_time`. Al terminar, retorna al estado `READY`.
* **TERMINATED (Terminado):** Estado de parada final donde el proceso se consolida en el historial analítico del sistema.

### Avance por Ticks de Reloj

El motor de simulación es conducido de forma centralizada por el método `execute_simulation_clock_cycle` dentro de la interfaz gráfica. El flujo exacto de ejecución en cada tick de reloj sigue un orden secuencial estricto:

1. **Admisión de Procesos:** Se evalúa la lista de procesos pendientes; aquellos cuyo tiempo de arribo coincida con el tick actual son inyectados en la cola de listos.
2. **Actualización de Bloqueados:** El planificador evalúa el conjunto `blocked_set`. Cada proceso bloqueado procesa su instrucción de reloj. Aquellos que agotan su tiempo de E/S son extraídos del conjunto y reencolados en la cola de listos.
3. **Paso de Tiempo en Espera:** Los procesos en la cola de listos avanzan su reloj interno acumulando tiempo de espera.
4. **Evaluación del Proceso en Ejecución:** Si la CPU no está ociosa, el proceso activo ejecuta un tick. Se verifican las condiciones de salida (Terminación, Interrupción voluntaria por E/S, o Expiración de Quantum / Preoridad si aplica).
5. **Políticas de Despacho:** Si la CPU queda vacía, el planificador aplica las reglas del algoritmo seleccionado para extraer el siguiente elemento de la cola de listos y otorgarle el contexto de ejecución.
6. **Sincronización Gráfica:** Se recalculan las métricas globales, se actualizan los listboxes dinámicos y se refresca el lienzo de Matplotlib antes de programar el siguiente ciclo.

---

## Análisis de Rendimiento

Para validar de forma científica el rendimiento de los algoritmos implementados, se generó un lote estocástico estático idéntico de **10 procesos** utilizando una distribución exponencial. Almacenar este lote en una réplica exacta de memoria (*benchmarking backup*) permite evaluar de manera equitativa cómo reacciona cada política ante la misma carga exacta de trabajo.

Los parámetros fijos de generación de la carga fueron:

* Media de Arribo (*Mean Arrival*): 4 ticks
* Media de Ráfaga de CPU (*Mean CPU Burst*): 6 ticks
* Media de Ráfaga de E/S (*Mean I/O Burst*): 3 ticks
* Quantum asignado (para Round Robin): 3 ticks

A continuación, se tabulan los resultados recolectados tras concluir la ejecución total del lote en cada uno de los algoritmos principales:

| Métrica de Rendimiento | FCFS | SJF (No Expulsivo) | SRTF (Expulsivo) | Non-Preemptive Priority | Preemptive Priority | Round Robin ($q=3$) | Random Selection |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Duración Total (Ticks)** | 61 | 83 | 82 | 67 | 90 | 71 | 99 |
| **Utilización de CPU (%)** | 77.0% | 96.4% | 86.6% | 89.6% | 91.1% | 93.0% | 86.9% |
| **Tiempo de Espera Promedio** | 4.0 | 12.1 | 5.5 | 8.1 | 21.0 | 11.9 | 28.5 |
| **Tiempo de Bloqueo Promedio** | 0.7 | 0.8 | 1.4 | 1.5 | 2.4 | 2.3 | 3.0 |
| **Tiempo de Retorno Promedio** | 9.0 | 20.4 | 13.6 | 15.2 | 31.1 | 20.3 | 39.5 |

### Análisis Comparativo de Resultados

* **FCFS (First-Come, First-Served):** Presentó el menor tiempo de espera promedio (4.0 ticks) y la menor duración total de la simulación (61 ticks), lo cual sugiere que el lote específico generado tuvo un orden de llegada favorable que minimizó la interacción o los solapamientos críticos en las ráfagas iniciales, aunque su utilización de CPU fue la más baja (77.0%), evidenciando periodos de inactividad prematuros o fragmentación por esperas de E/S.
* **SJF (Shortest Job First) y SRTF (Shortest Remaining Time First):** SJF maximizó de forma sobresaliente la utilización de la CPU (96.4%), manteniendo a los procesos en el procesador con alta densidad, pero a costa de elevar el tiempo de espera promedio a 12.1 ticks. SRTF logró un balance más equilibrado con una utilización del 86.6% y un tiempo de espera muy competitivo de 5.5 ticks, demostrando la efectividad de la expulsión (*preemption*) para recortar los tiempos de respuesta ante cargas dinámicas.
* **Políticas de Prioridad (Preemptive vs Non-Preemptive):** El algoritmo expulsivo por prioridades (*Preemptive Priority*) penalizó severamente a los procesos de baja prioridad, disparando el tiempo de espera promedio a 21.0 ticks y extendiendo la duración total a 90 ticks. La variante no expulsiva (*Non-Preemptive Priority*) contuvo mejor estos indicadores (8.1 de espera y 67 ticks totales), reflejando que los cambios de contexto forzados por criterios de prioridad externos al tamaño de ráfaga pueden degradar la agilidad general del sistema.
* **Round Robin ($q=3$):** Demostró un excelente comportamiento adaptativo en un entorno intermitente, registrando una utilización de CPU muy alta (93.0%) y una duración total controlada de 71 ticks. Esto confirma la efectividad teórica del tiempo compartido para mantener el procesador activo alternando equitativamente entre ráfagas de cómputo y transiciones de E/S.
* **Random Selection:** Consistente con las expectativas teóricas, la selección aleatoria arrojó el peor rendimiento global, con la mayor duración total (99 ticks) y el tiempo de espera promedio más alto (28.5 ticks), validando la necesidad matemática de contar con políticas de planificación estructuradas.
---

## Desafíos de Implementación y Soluciones

El desarrollo de un simulador con ráfagas concurrentes de CPU y E/S presentó desafíos lógicos críticos que requirieron soluciones arquitectónicas específicas:

### Sincronización del Comportamiento Intermitente de E/S

* **El Desafío:** En los sistemas operativos reales, los procesos realizan llamadas al sistema de E/S de forma impredecible en medio de sus ráfagas de cómputo. Modelar esto de manera determinista al inicio del proceso rompía el dinamismo de las colas.
* **La Solución:** Se diseñó una estrategia estocástica de rendimiento intermitente dentro de `process_scheduler.py`. Mientras un proceso está en estado `RUNNING`, posee una probabilidad del 15% en cada tick de activar una interrupción voluntaria para ceder la CPU hacia el subsistema de E/S (`force_io_yield`). Para evitar bucles infinitos de bloqueo, se introdujo la bandera booleana `has_yielded_io` en el PCB, asegurando que cada proceso transicione al set de bloqueo como máximo una vez en su ciclo de vida, emulando fielmente un esquema de comportamiento mixto.