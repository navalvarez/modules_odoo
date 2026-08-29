# Tipo de Cambio Bolivia

Actualización automática del tipo de cambio y UFV en Odoo 16 Community mediante los servicios web del Banco Central de Bolivia (BCB).

# Características

* Consulta del tipo de cambio oficial del dólar.
* Consulta del valor de la UFV.
* Integración mediante servicio web SOAP del BCB.
* Actualización automática mediante una acción planificada.
* Registro de las tasas con su fecha correspondiente.
* Compatible con Odoo 16 Community.
* Sin necesidad de API Key.
* Diseñado para instalaciones de Odoo con servidor propio u Odoo.sh.

# Fuente de información

Los datos son obtenidos mediante los servicios web del:

**Banco Central de Bolivia (BCB)**


# Funcionamiento

El módulo consulta los indicadores económicos del BCB y actualiza las tasas de cambio configuradas en Odoo.

El proceso puede ejecutarse automáticamente mediante una acción planificada de Odoo.

Ejemplo de funcionamiento:

1. Odoo ejecuta la acción planificada.
2. El módulo consulta el servicio web del BCB.
3. Se obtiene el tipo de cambio y/o UFV.
4. Se registra la tasa correspondiente con su fecha.
5. La información queda disponible para las operaciones de Odoo.

# Actualización automática

El módulo incluye una acción planificada para realizar la actualización periódicamente.

La frecuencia puede modificarse desde:

**Ajustes > Técnico > Acciones planificadas**

Se recomienda programar la actualización una vez al día.

# Instalación

#. Copiar el módulo `tipo_de_cambio_bob` dentro del directorio de addons.
#. Reiniciar el servidor de Odoo.
#. Activar el modo desarrollador.
#. Actualizar la lista de aplicaciones.
#. Buscar **Tipo de Cambio Bolivia**.
#. Instalar el módulo.

# Requisitos

* Odoo 16.0 Community
* Módulo `base`
* Módulo `account`
* Conexión a Internet desde el servidor de Odoo para acceder al servicio web del BCB.

# Compatibilidad

+----------------------+------------------+
| Plataforma           | Odoo 16          |
+----------------------+------------------+
| Edición              | Community        |
+----------------------+------------------+
| País                 | Bolivia          |
+----------------------+------------------+
| Actualización        | Automática       |
+----------------------+------------------+

# Importante

La disponibilidad y exactitud de los valores dependen del servicio proporcionado por el Banco Central de Bolivia.

El módulo no modifica los valores históricos de forma indiscriminada y registra las tasas asociadas a su fecha correspondiente.

# Licencia

Other Proprietary
