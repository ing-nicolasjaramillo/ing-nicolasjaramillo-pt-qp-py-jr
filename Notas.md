# Hallazgo

* El hecho de que la función Round() no funcionaría me llamó mucha la atención debido a que es una función que he utilizado muchas veces y descubrí que no la conocía tanto como creía.
* Dependencias sin versión fija dentro del 'requirements.txt': encontré que  aceptaba cualquier versión reciente, y al instalar llegaron versiones nuevas que generan advertencias, y como el proyecto trata  las advertencias como errores, los tests al inicio ni siquiera cargaban
* El enunciado mencionaba que la fechas debían venir acompañadas de su zona horaria, pero esto no siempre ocurría, lo que hacía imposible saber si dos horas eran realmente iguales
* Que en el método calcular_tarifa tuviera quemado el valor para el tipo, esto no debería estar en ese metodo como una cadena, sino llamarse desde el config como ocurre con DESCUENTOS, MULTIPLO_REDONDEO,TARIFA_BASE; ya que el día de mañana al sistema se le integran nuevas funciones haciendolo más complejo y será más difíficil hacer un cambio. 
* Había un test que no probaba nada: el test de historial verificaba `>= 1`, por eso este pasaba
  aunque el historial tuviera cálculos de otras tarjetas (El bug).

# Casos borde y cómo los resolví

- Validaciones desordenadas y con zonas mezcladas (Z y -05:00): se ordenan y comparan
  por instante real, no por el texto y finalmente se devuelven en orden cronologico.
- Ventana de 90 minutos: se mide desde el inicio del viaje, no desde la validación
  anterior, además el minuto 90 exacto cuenta como transbordo.
- Tercer transbordo y viajes que cruzan medianoche: abren viaje nuevo / se tratan igual, porque se resta instante contra instante.
- Redondeo en la mitad exacta (325 -> 350, 225 -> 250): cálculo con enteros.
- Entradas inválidas -> Código 422: fecha sin zona, id repetido, mismo instante con distinto id,
  perfil inválido, null o vacío ("").
- Todos los cascos tienen un test en tests/test_transbordos.py; la tabla completa está en Bitacora.md (Sección 1.7).

# Supuestos
- Mismo instante con distinto id -> Respuesta 422. No estaba en la lista del enunciado; lo consulté
  por el canal de preguntas pero no obtuve respuesta en el tiempo en el que solucioné la prueba por lo que bajo mi criterio la agregué.
- perfil: null o "" -> Respuesta 422. Solo la ausencia del campo tendrá el valor de general.
- fecha_hora se devuelve con la misma zona horaria con que llegó.

# Qué dejarías para después si esto fuera a producción.
Me llama la atención que los datos pueden llegar tarde por falta de conectividad, por lo que si un cobro se genera y hubo algún problema con una validación puede modificarse el valor de dicho cobro, creando un problema, sin embargo es un tema que puede salir del alcance del software, por lo que me enfocaría principalmente en dos puntos:

1. Mejorar la persistencia de los datos en una base de datos: Actualmente no se guarda rastro de las validaciones y en cada ejecución nueva del servicio se vacía de memoria, además si dos máquinas o servidores lanzaran cada uno el servicio no habría una fuente de datos centralizada sino que cada uno tendría su propio historial y una consulta puede no encontrar los cálculos de una tarjeta.

2. Autenticación para consultar el historial de tarjetas: Siguiendo con el hilo del bug reparado en el ejercicio de la prueba, buscamos que una persona dueña de una tarjeta no vea historial de otras personas, por lo que implementaría esta capa de seguridad que asegure la confidencialidad de los datos.