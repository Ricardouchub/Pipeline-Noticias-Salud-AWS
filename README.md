# Pipeline de Datos de Noticias de Salud en AWS

Este proyecto implementa un pipeline de datos 100% serverless en AWS para recolectar, procesar, almacenar y generar alertas sobre noticias relacionadas con enfermedades virales como `virus`, `influenza`, `brote`, etc. El sistema está diseñado para ser automático, seguro y escalable, utilizando la computación en la nube.

## Características Principales

* **Recolección Diaria Automatizada:** El pipeline se ejecuta automáticamente cada día para buscar las noticias más recientes.
* **Múltiples Fuentes de Datos:** Extrae información de tres APIs de noticias diferentes (`GNews`, `NewsAPI`, `Newsdata.io`) para una cobertura más amplia.
* **Procesamiento y Estandarización:** Limpia, unifica el formato y elimina artículos duplicados para asegurar la calidad de los datos.
* **Almacenamiento Persistente y Seguro:** Guarda los artículos en una base de datos (PostgreSQL) dentro de una red privada.
* **Alertas por Correo Electrónico:** Envía un resumen diario por email con los artículos nuevos que se han encontrado.
* **Arquitectura Segura:** Todos los componentes críticos operan dentro de una VPC, y las credenciales se gestionan de forma segura.

##  Arquitectura y Flujo de Trabajo

El pipeline sigue un flujo de datos claro y orquestado por servicios de AWS.

[AQUÍ VA EL DIAGRAMA DE FLUJO DEL PIPELINE]

El proceso funciona de la siguiente manera:

1.  **Disparador:** Cada día a una hora programada, **Amazon EventBridge** activa la función Lambda.
2.  **Ejecución:** La función **AWS Lambda** se inicia dentro de la VPC y comienza su trabajo:
    * **Configuración Segura:** Se conecta a **AWS Parameter Store** para obtener las claves de las APIs y el email del destinatario.
    * **Salida a Internet:** Utiliza un **NAT Gateway** para conectarse de forma segura a la internet pública y llamar a las tres APIs de noticias.
    * **Procesamiento:** Recibe las respuestas, estandariza los artículos a un formato común y elimina los duplicados.
3.  **Almacenamiento:**
    * La función Lambda obtiene la contraseña de la base de datos desde **AWS Secrets Manager**.
    * Se conecta a la base de datos **Amazon RDS (PostgreSQL)**, que también está en la red privada.
    * Inserta únicamente los artículos que no existían previamente, gracias a una restricción `UNIQUE` en la URL del artículo.
4.  **Alerta:**
    * Si se guardaron artículos nuevos en la base de datos, la función Lambda utiliza **Amazon SES** para formatear y enviar un correo electrónico de resumen al destinatario configurado.

## Herramientas y Servicios de AWS

* **AWS Lambda:** El núcleo del pipeline, donde se ejecuta todo el código Python para la extracción, transformación y carga (ETL).
* **Amazon EventBridge:** El orquestador serverless que actúa como un "cron job" para ejecutar la Lambda diariamente.
* **Amazon RDS (PostgreSQL):** Provee la base de datos relacional gestionada y persistente donde se almacenan los artículos.
* **Amazon VPC:** La red virtual privada que aísla y protege todos nuestros recursos de la internet pública.
    * **Subredes Públicas y Privadas:** Para separar los recursos que necesitan acceso a internet (NAT Gateway) de los que no (Lambda, RDS).
    * **NAT Gateway:** Permite que los recursos en subredes privadas (como la Lambda) inicien conexiones a internet sin exponerse a conexiones entrantes.
    * **Internet Gateway:** Proporciona la conexión a internet para la VPC.
    * **Tablas de Rutas:** Dirigen el tráfico de red entre las subredes, el NAT Gateway y el Internet Gateway.
* **AWS IAM (Identity and Access Management):** Gestiona todos los permisos y roles para que los servicios puedan comunicarse entre sí de forma segura.
* **AWS Systems Manager Parameter Store:** Almacena de forma segura la configuración no secreta, como las claves de las APIs y el email del destinatario.
* **AWS Secrets Manager:** Almacena de forma segura las credenciales de la base de datos.
* **Amazon SES (Simple Email Service):** Gestiona el envío de las alertas por correo electrónico.
* **Amazon EC2 (Bastion Host):** (Opcional para operación, pero necesario para administración) Un pequeño servidor que actúa como un "puente" seguro para que un desarrollador pueda conectarse a la base de datos privada con herramientas como DBeaver.

## Resultado Final

El resultado final del pipeline es doble:

1.  Una **base de datos en RDS** que se actualiza diariamente con noticias curadas sobre temas de salud, lista para ser utilizada en proyectos de análisis, visualización o ciencia de datos.
2.  Un **correo electrónico de alerta** que se envía al usuario cada día que se encuentran noticias nuevas, proporcionando un resumen inmediato y accesible.

##  Cómo Desplegar el Proyecto

Para replicar este proyecto, sigue estos pasos:

    1. Requisitos:
      * Una cuenta de AWS.
      * Python 3.10+ instalado localmente.
      * AWS CLI configurada.
      * Git.

    2. Configuración del Entorno:
      * Clona este repositorio.
      * Crea y activa un entorno virtual de Python: `python3 -m venv venv` y `source venv/bin/activate`.
      * Instala las dependencias: `pip install -r requirements.txt`.

    3. Configuración en AWS:
      * Crea los parámetros en **Parameter Store** para las claves de API y el email.
      * Verifica tu identidad de correo electrónico en **Amazon SES**.
      * Crea una base de datos **RDS PostgreSQL** en una VPC.
      * Guarda las credenciales de la base de datos en **Secrets Manager**.
      * Configura la red (NAT Gateway, tablas de rutas, etc.) como se discutió.

    4. Despliegue de la Lambda:
      * Añade las librerías necesarias a una carpeta `package`.
      * Crea un archivo `.zip` con tu código (`main.py`) y las librerías.
      * Crea la función Lambda, configúrala para usar la VPC y las subredes privadas.
      * Añade la capa (Layer) pública de `psycopg2`.
      * Sube el archivo `.zip`.
      * Crea la regla en **EventBridge** para disparar la función diariamente.

## Posibles Mejoras a Futuro

* **Análisis y Visualización:** Conectar herramientas como Tableau, Power BI o Amazon QuickSight a la base de datos para crear dashboards interactivos.
* **Machine Learning:** Aplicar modelos de Procesamiento de Lenguaje Natural (PLN) para análisis de sentimiento, clasificación de temas o detección de anomalías en la frecuencia de noticias.
* **Optimización de Costos:** Configurar alertas de presupuesto y analizar los logs para optimizar el uso de los recursos.
