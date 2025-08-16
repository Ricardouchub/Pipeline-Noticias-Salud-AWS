# Pipeline de Datos de Noticias de Salud en AWS

Este proyecto implementa un pipeline de datos 100% serverless en AWS para recolectar, procesar, almacenar y generar alertas sobre noticias relacionadas con enfermedades virales como `virus`, `influenza`, `brote`, etc. El sistema está diseñado para ser automático, seguro y escalable, utilizando la computación en la nube.

---

## Características Principales

* **Recolección Diaria Automatizada:** El pipeline se ejecuta automáticamente cada día para buscar las noticias más recientes de múltiples fuentes, en este caso, tres APIs de noticias diferentes (`GNews`, `NewsAPI`, `Newsdata.io`) para una cobertura más amplia.
* **Procesamiento y Estandarización:** Limpia, unifica el formato y elimina artículos duplicados para asegurar la calidad de los datos.
* **Almacenamiento Persistente y Seguro:** Guarda los artículos en una base de datos (PostgreSQL) dentro de una red privada.
* **Alertas por Correo Electrónico:** Envía un resumen diario por email con los artículos nuevos que se han encontrado.
* **Arquitectura Segura:** Todos los componentes críticos operan dentro de una VPC, y las credenciales se gestionan de forma segura.

##  Arquitectura y Flujo de Trabajo

El pipeline sigue un flujo de datos claro y orquestado por servicios de AWS.

<img width="1788" height="376" alt="image" src="https://github.com/user-attachments/assets/f6911cfa-93c7-40bc-bf02-be18a9e4ba31" />

---
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


## Estructura del Repositorio

* **`main.py`**: Script principal de Python que contiene toda la lógica para la función AWS Lambda. Se encarga de la extracción de datos desde las APIs, la transformación (limpieza y estandarización) y la carga (guardado en la base de datos y envío de correo).
* **`requirements.txt`**: Libreridas y dependencias necesarias.


## Autor

**Ricardo Urdaneta**

[LinkedIn](https://www.linkedin.com/in/ricardourdanetacastro)

## Vista de base de datos con artículos extraidos usando DBeaver
<img width="2222" height="1028" alt="image" src="https://github.com/user-attachments/assets/3a870d61-f6c0-4988-9375-da63d66f979b" />

