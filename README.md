# Simulador de Planificación de Procesos CPU (Multi-Política)

Esta herramienta interactiva ha sido desarrollada en Python utilizando **Tkinter** y **Matplotlib** para modelar, analizar y visualizar en tiempo real el comportamiento de diversos algoritmos de planificación de procesos de un sistema operativo, tanto de naturaleza **no expulsiva (non-preemptive)** como **expulsiva (preemptive)**.

---

## Características Principales

* **Interfaz Gráfica Intuitiva:** Paneles segmentados para configuraciones de infraestructura, telemetría analítica y vistas discretas de colas.
* **Visualización en Tiempo Real:** Gráfico de tendencias en vivo que renderiza la fluctuación del volumen de procesos por cada estado del sistema.
* **Modelado Estocástico de Cargas de Trabajo:** Generación automática de ráfagas y tiempos de llegada mediante distribuciones estadísticas exponenciales.
* **Análisis Comparativo Exhaustivo:** Almacenamiento y ejecución de lotes idénticos en réplicas exactas de memoria para realizar evaluaciones de rendimiento equitativas (*benchmarking*) entre algoritmos.

---

## Arquitectura y Estructuras de Datos

El diseño de software sigue principios de modularidad y orientación a objetos distribuidos de la siguiente manera:

* `process.py` (**Clase Process**): Modela el bloque de control del proceso (PCB). Registra métricas de tiempo y controla la máquina de estados discreta del ciclo de vida del proceso (`READY`, `RUNNING`, `BLOCKED`, `TERMINATED`).
* `process_scheduler.py` (**Clase ProcessScheduler**): El motor central que encapsula las estructuras de colas dinámicas (listas nativas y conjuntos `set`) y las reglas lógicas que gobiernan cada algoritmo de planificación.
* `process_generator.py` (**Clase ProcessGenerator**): Módulo responsable de inyectar entropía controlada al sistema simulando la creación de flujos reales de procesos.
* `gui.py` (**Clase SchedulerGUI**): Orquestador de la UI que sincroniza la tasa de refresco del procesador mediante bucles de eventos asíncronos (`root.after`).
* `main.py`: Punto de entrada del programa.

---

## Parámetros de Simulación y Generación

Para simular una carga de trabajo realista, el sistema requiere los siguientes parámetros de configuración:

* **Algoritmo:** La política de planificación que determinará el orden de despacho de la CPU.
* **Quantum (Ticks):** El intervalo de tiempo máximo continuo asignado a un proceso en políticas de tiempo compartido (Round Robin).
* **Workloads (Cantidad de Procesos):** El número total de procesos individuales a generar para la prueba.
* **Mean Arrival (Media de Arribo):** Controla el intervalo estocástico promedio entre las llegadas de nuevos procesos al sistema.
* **Mean CPU Burst (Media de Ráfaga de CPU):** El ciclo de ejecución promedio que requiere el proceso en la CPU antes de terminar o pasar a E/S.
* **Mean I/O Burst (Media de Ráfaga de E/S):** El tiempo promedio que un proceso permanecerá bloqueado esperando la resolución de un recurso de entrada/salida.
* **Latency (ms):** Define la duración en milisegundos de cada "Tick" (paso del reloj) en el simulador para acelerar o ralentizar la inspección visual.

---

## Algoritmos Implementados

### Políticas No Expulsivas (Non-Preemptive)

Un proceso mantiene el control de la CPU de forma ininterrumpida hasta que finaliza voluntariamente su ejecución o cede el control para realizar operaciones de E/S.

* **FCFS (First-Come, First-Served):** Los procesos se despachan estrictamente en el orden cronológico en que ingresan a la cola de listos.
* **SJF (Shortest Job First):** Selecciona prioritariamente el proceso en la cola de listos que posea la ráfaga de CPU restante más corta. Evita retrasos de procesos ligeros tras tareas masivas (Efecto Convoy).
* **Planificación Basada en Prioridades:** Despacha el proceso con el nivel numérico de prioridad más alto asignado (donde valores numéricos más bajos representan mayor jerarquía).
* **Selección Aleatoria (Random):** El planificador extrae un proceso al azar de la cola de listos en cada ciclo de inactividad de la CPU, sirviendo como métrica base de control aleatorio.

### Políticas Expulsivas (Preemptive)

El planificador puede interrumpir activamente el proceso en ejecución si las condiciones del sistema cambian o si se agota su tiempo asignado.

* **Round Robin (Turno Rotativo):** Cada proceso recibe un segmento equitativo de tiempo (Quantum). Al expirar el contador, el proceso es devuelto al final de la cola y se despacha el siguiente.
* **SRTF (Shortest Remaining Time First):** Variante expulsiva de SJF. Si un nuevo proceso arriba a la cola con un tiempo restante menor que el del proceso actualmente en ejecución, este último es interrumpido y devuelto a la cola.
* **Planificación Basada en Prioridades (Preemptivo):** Si un proceso con una prioridad de mayor jerarquía ingresa a la cola de listos, interrumpe de inmediato al proceso que está corriendo en la CPU.

> ⚠️ **Nota de Diseño de E/S:** El simulador integra una estrategia de rendimiento realista donde los procesos tienen una probabilidad del **15%** en cada paso del reloj de realizar una interrupción voluntaria para ceder el control al subsistema de E/S (`BLOCKED`), volviendo a la cola de `READY` tras cumplir su ráfaga de bloqueo.

---

## Métricas de Rendimiento Analítico

El panel de **Live Performance Telemetry Summary** calcula y actualiza dinámicamente:

$$\text{Utilización de CPU} = \left( \frac{\text{Ticks Activos de CPU}}{\text{Tick Actual de Simulación}} \right) \times 100$$

* **Tiempo Promedio de Espera (Avg Waiting Time):** Tiempo acumulado por los procesos en estado `READY` esperando ser despachados.
* **Tiempo Promedio de Bloqueo (Avg Blocked Time):** Tiempo medio invertido por los procesos en el set de E/S (`BLOCKED`).
* **Tiempo Promedio de Retorno/Turnaround (Avg Turnaround):** El intervalo total transcurrido desde el instante exacto de arribo de un proceso hasta su finalización definitiva (`TERMINATED`).
* **Contadores de Micro-Colas:** Totales numéricos dinámicos de procesos en tránsito en cada sección de la infraestructura del sistema operativo.

---

## Instalación y Ejecución

### Prerrequisitos

Asegúrate de contar con Python 3.8+ instalado en tu sistema junto con el gestor de paquetes `pip`.

### Instalación de Dependencias

Instala la biblioteca requerida para la visualización gráfica de datos:

```bash
pip install matplotlib

```

### Ejecutar el Simulador

Para iniciar la aplicación, ejecuta el script principal desde la raíz de los archivos:

```bash
python3 main.py

```

---

## 📋 Instrucciones de Uso

1. **Configura los parámetros** de carga de trabajo en el panel superior (puedes dejar los valores por defecto optimizados).
2. Haz clic en **"Generate Workload"** para crear el lote estocástico inicial. Podrás observar los datos generados ordenados en el *Global Workload Ledger*.
3. **Selecciona un algoritmo** de la lista desplegable y ajusta el deslizador de latencia según tu preferencia de velocidad de inspección.
4. Presiona **"Start Simulation"** para observar el movimiento en tiempo real de las colas discretas y las fluctuaciones en la matriz gráfica.
5. Puedes detener la ejecución en cualquier momento presionando **"Stop / Reset"**. Al reiniciar la simulación con una política diferente, **se aplicará exactamente el mismo lote original**, permitiéndote contrastar de manera científica qué algoritmo gestiona mejor la misma carga de trabajo.