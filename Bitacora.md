Propósito : Esta bitacora es un análisis del contexto de la prueba, y tiene como propósito funcionar como SDD o fuente de verdad, a partir de este análisis se va a construir la solución utilizando Opencode.

# 1 . Análisis e interiorización general 

Antes de tocar codigo lo primero es comprender el contexto actual, cómo funcionan los viajes actualmente, cómo se realizan los cobros, cómo llegan los datos, cómo se está respondiendo a las peticiones.
Una vez comprendido esto, el enfoque es sobre la nueva funcionalidad, qué cambios tendrá, qué se debe agregar, cuáles es la nueva categoria que se va a implementar, qué perfiles, qué descuentos, qué reglas tendrá.
Finalmnte se analiza el código actual heredado, qué archivos tenemos, las funciones existentes, cómo es la lógica actual, qué responsabilidades tenemos.

## Resumen de lo que hay que hacer
- Integrar la nueva funcionalidad de tarifa transbordo
- Solucionar el bug que tiene un usuario al consultar el historial de su tarjeta le aparecen cálculos de otras tarjetas.
- Verificar que el servicio corra con Docker

# Tarea 1: FEATURE TRANSBORDO

## 1.2 . Anotaciones generales

14 estaciones

Costo de 1 viaje actualmente $3200

Validacion = cada vez que la tarjeta pasa por un torniquete.
Viaje = empieza con una validación que paga tarifa. Dura 90 minutos contados desde esa primera validación
Qué es un transbordo? Es un segundo o tercer recorrido que ocurre dentro los 90 minutos a partir de la primera tarifa
<!-- --------------------------------------------------------------------- -->
Perfiles y descuentos
general -> 0% 
estudiante -> 35%
adulto_mayor -> 55%
<!-- --------------------------------------------------------------------- -->
validacion(viajes)|tipo
1er : tarifa-> descuento según perfil (0,35 o 55)
2do : transbordo -> 500
3er : transbordo_gratis -> gratis
4to : se reinicia el proceso y se considera viaje inicial (tarifa)

Los descuentos se aplican a cada validacion
<!-- --------------------------------------------------------------------- -->

Los redondeos se al multiplo de 50 más cercano, si queda en la mitad aproxima hacia arriba. No usar round()
Ejemplo: estudiante, transbordo: 325 → 350
Asignar los posibles valores que puede tener "tipo" (tarifa, transbordo, transbordo_gratis) en la respuesta
<!-- --------------------------------------------------------------------- -->

## 1.3 Restricciones: 
- Lo descuentos se hacen según el perfil y aplican a cada cobro (cada registro que venga en validaciones)
- No pueden haber dos validaciones con el mismo id
- En una tarjeta no pueden haber dos validaciones con diferente id pero mismo instante de fecha_hora, ya que no puede viajarse desde dos sitios al mismo instante, si ocurre es un error. debe compararse por instante, no por texto. 11:58:27Z y 06:58:27-05:00 son el mismo momento 
- Si llega una petición con "perfil" distinto a los 3 permitidos lanza error
- Si no llega el campo perfil, se considera general

## 1.4 Validaciones
- Se debe validar que fecha_hora este en el formato esperado
- se debe validar que fecha_hora trae zona horaria de lo contrario lanza error
- "tipo" debe tener un valor de los tres posibles (tarifa, transbordo, transbordo_gratis)
- Validar que "valor" y "total" sean pesos y enteros
- Se debe validar si "perfil" no viene entonces se asigna el valor general
- Se debe validar si "perfil" viene vacío "" o null; se responde con el error 422
- Se debe validar si "perfil" no viene vacío, entonces debe tener uno de los 3 valores posibles (general, estudiante, adulto_mayor)


## 1.5 Asignación de tipo de viaje (tarifa, transbordo, transbordo_gratis)

El cálculo se hace sobre las "validaciones" ya ordenadas cronológicamente y lleva dos datos de estado: 'inicio_viaje' (fecha_hora de la validación que abrió el viaje) y transbordos_usados (0, 1 o 2)

- Sin viaje abierto: (es la primera de la lista) -> tarifa. 
    Se abre el viaje: inicio_viaje = esta validación y transbordos_usados = 0.
- Diferencia con inicio_viaje > 90 min → tarifa. Se abre viaje nuevo.
- Diferencia ≤ 90 min y transbordos_usados = 0 -> transbordo; transbordos_usados += 1.
- Diferencia ≤ 90 min y transbordos_usados = 1 -> transbordo_gratis transbordos_usados = 2.
- Diferencia ≤ 90 min y transbordos_usados = 2 -> tarifa. Se abre viaje nuevo.

## 1.6 Datos de ejemplo (validaciones_03-10.json)
Las validaciones no llegan ordenadas cronológicamnte
Hay diferencias entre las zonas de una misma tarjeta
Existen viajes que pueden estar en el limite de 90 min pero que pase de un día a otro
Los cobros se devuelven ordenadas cronológicamente

## 1.7 Casos borde

| Caso | Resultado esperado |
|---|---|
| Sin validaciones | 200, `cobros: []`, `total: 0` |
| Una sola validación | 1 cobro `tarifa` |
| Validación exactamente a 90:00 del inicio | `transbordo` |
| Validación a 90:01 del inicio | `tarifa` |
| 0:00 → 1:00 → 2:00 | `tarifa`, `transbordo`, `tarifa` |
| 4 validaciones dentro de 90 min | `tarifa`, `transbordo`, `transbordo_gratis`, `tarifa` |
| Viaje nuevo tras el 3er intento: la siguiente validación dentro de 90 min de **ese** inicio | `transbordo` |
| Validaciones desordenadas en la entrada | Se calculan y devuelven en orden cronológico |
| Zonas horarias mezcladas (`Z` y `-05:00`) en la misma tarjeta | Se comparan por instante real |
| Viaje que cruza medianoche | Se trata igual que cualquier otro |
| `fecha_hora` sin zona horaria | 422 |
| `id` repetido | 422 |
| `perfil` inválido o en mayúscula | 422 |
| `perfil` ausente | `general` |
| Redondeo en la mitad exacta | Sube |
| `transbordo_gratis` con descuento | 0 |
| Misma estación dos veces dentro de la ventana | Cuenta como `transbordo`; la estación no influye |
| Misma instante de `fecha_hora` con distinto `id` | 422 |

## 1.8 Supuestos
Misma instante de fecha_hora con distinto id.se responde con código 422 y se rechaza.
perfil: null o "" Se trata como inválido (422). Solo la ausencia del campo en la solicitud equivale a 'general'.
fecha_hora en la respuesta se devuelve con la misma zona horaria con que llegó, sin convertirla a ningún estandar

## 1.9 Plan de implementación (un commit por paso)
1. **Modelos** (`modelos.py`): `fecha_hora` que exija zona horaria; `tipo` cerrado a los tres valores; validar `id` duplicados en `SolicitudTarifa`.
2. **Redondeo** (`tarifas.py`): `aplicar_descuento` con aritmética entera y mitad hacia arriba. Generalizarlo para que sirva a tarifa y transbordo.
3. **Asignación de tipos** (`tarifas.py`): ordenar por instante y aplicar la lógica de 1.5. Usar `VALOR_TRANSBORDO` y `VENTANA_TRANSBORDO_MIN` de `config.py`; no escribir valores fijos en el código.
4. **Tests**: un test por cada caso borde (1.7), más el ejemplo oficial (T-004417 → 3.200 + 500 = 3.700).

## 1.10 Restricciones para la IA
- No modificar el contrato del endpoint (nombres, tipos, estructura).
- Consultar antes de modificar cualquier archivo.
- No tocar `pyproject.toml`: los warnings se tratan como errores y no se desactiva.
- No adelantar la Tarea 2 (BUG-17).

## 1.11 Fuera de alcance
- Los datos llegan cuando hay señal, así que un error no se detecta en el instante en que ocurre.
- No es posible saber si dos personas usan la misma tarjeta. Dos pases con 10 s de diferencia tienen id y fecha_hora distintos, y el sistema los cobra como `tarifa` + `transbordo`.
- Se espera que las fechas vengan correctamente pero se valida de todos modos


# Tarea 2: CORREGIR BUG

## 2.1 Descripción error
Al consultar el método GET /tarjetas/{tarjeta}/historial aparecen cálculos de otras tarjetas.
Pasa en producción; en local, con una sola tarjeta, no se reproduce.

## 2.2 Origen 
En app/historial.py la lista calculos está declarada en el cuerpo de la clase HistorialTarjeta, no dentro de '__init__':
Ejemplo:
    class HistorialTarjeta:
        calculos: list[RespuestaTarifa] = []   # atributo de CLASE

Un atributo de clase existe una unica vez y lo comparten todas las instancias, a pesar de que 'obtener_historial' crea un HistorialTarjeta distinto por tarjeta, todos apuntan a un misma lista. Cada 'registrar()' hace '.append' sobre esa lista compartida, y 'listar()' devuelve todo lo que haya dentro de ella, sin importar de qué tarjeta venga la consulta.

Parece correcto porque la sintaxis 'campo: tipo = valor' se usa en Pydantic y dataclasses, donde cada instancia sí recibe su copia. Pero HistorialTarjeta es una clase normal de Python.

## 2.3 ¿Por que no se reproducía en local ?
Al tratar de recrearse con una sola tarjeta en local, todos los cálculos de la lista compartida son de esa tarjeta, entonces la mezcla no se nota. Se  ecesitan al menos dos tarjetas distintas para verla.

## 2.4 Por qué el test existente no lo detectó
test_historial_registra_el_calculo usa una sola tarjeta y verifica 'len(...) >= 1'. Pasa aunque el historial tenga cálculos de otras tarjetas.

## 2.5 Solución propuesta
Mover 'calculos' al '__init__' como un atributo de instancia ('self.calculos = []'), para que cada HistorialTarjeta tenga su propia lista.
Cambio mínimo: no se toca main.py ni el contrato del endpoint.

## 2.6 Cómo verificar si se corrigió el bug
Test de API: calcular para dos tarjetas distintas (A y B) y verificar que:
- el historial de A tiene exactamente sus cálculos y todos son de la tarjeta A;
- el historial de B tiene exactamente los suyos y no hay ninguno de A.
Debe fallar antes de la corrección y pasar después.

## 2.7 Plan (un commit por paso)
1) Test que reproduce el bug (en rojo).
2) Corrección en historial.py y testear neuvamente (test en verde).

## 2.8 Fuera de alcance
- Actual historial vive no persiste, este se pierde al reiniciar el servicio.
- Con varios procesos (workers) cada uno tendría su propio historial.
- No hay control de concurrencia sobre el diccionario global '_historiales'.
- Los tests comparten estado global entre sí; idealmente se limpiaría entre tests.

# Tarea 3: DOCKER

## 3.1 Prueba de funcionamiento
Actualmente al levantar el contenedor para comprobar nos encontramos que el servicio uvicorn se expone dentro del contenedor en la dirección lookpback (127.0.0.1) pero no es accesible desde la máquina host, lo que deja en evidencia que es necesario ajustar la dirección por la cual se expone el servicio.

Además, al apoyarme en Claude para el análisis de la salida al levantar el contenedor, comprendí que actualmente se está copiando archivos innecesarios a la imágen, como el entorno virtual, el contenido de .git, pytest_cache y el contexto de .opencode; por lo que se puede optimizar mucho la imágen.

## 3.2 Solución
Para solucionar la primera situación se debe modificar el Dockerfile y agregar '--host 0.0.0.0' al comando de uvicorn. Esto significa que se reciben peticiones por cualquier entrada del contenedor, permitiendo acceder desde la maquina host.
Además se modifica docker-compose.yml para limitar el aceeso del puerto "127.0.0.1:8000:8000". Así se agrega seguridad para la práctica, limitando a que solo se pueda abrir desde la máquina host.

y para la solución de la segunda situación, se crea un .dockerignore para agregar todo lo que no es contexto necesario para la imagen, haciendolo más liviano.
