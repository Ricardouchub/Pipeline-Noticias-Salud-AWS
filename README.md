# Sistema de Monitoreo y Alertas de Salud con un Pipeline de Datos Serverless en AWS

<p align="left">
  <!-- Estado del proyecto -->
  <img src="https://img.shields.io/badge/Project_Status-Completado-2ECC71?style=flat-square&logo=checkmarx&logoColor=white" alt="Project Status: Completed"/>

  <!-- Lenguaje y librerías -->
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/boto3-AWS_SDK-FF9900?style=flat-square&logo=amazonaws&logoColor=white" alt="boto3"/>
  <img src="https://img.shields.io/badge/psycopg2-Postgres_Adapter-336791?style=flat-square&logo=postgresql&logoColor=white" alt="psycopg2"/>
  <img src="https://img.shields.io/badge/Requests-HTTP_Client-EE4C2C?style=flat-square&logo=python&logoColor=white" alt="Requests"/>

  <!-- AWS Core -->
  <img src="https://img.shields.io/badge/AWS_Lambda-ETL_Functions-FF9900?style=flat-square&logo=awslambda&logoColor=white" alt="AWS Lambda"/>
  <img src="https://img.shields.io/badge/Amazon_EventBridge-Scheduler-FF9900?style=flat-square&logo=amazoneventbridge&logoColor=white" alt="Amazon EventBridge"/>
  <img src="https://img.shields.io/badge/Amazon_RDS-PostgreSQL-FF9900?style=flat-square&logo=amazonrds&logoColor=white" alt="Amazon RDS"/>
  
  <!-- Notifications & Ops -->
  <img src="https://img.shields.io/badge/Amazon_SES-Email_Service-FF9900?style=flat-square&logo=amazonses&logoColor=white" alt="Amazon SES"/>
  <img src="https://img.shields.io/badge/Amazon_EC2-Bastion_Host-FF9900?style=flat-square&logo=amazonec2&logoColor=white" alt="Amazon EC2"/>
</p>

Este proyecto implementa una solución de datos de extremo a extremo en AWS. Consiste en dos fases principales:
1.  Un **pipeline de datos** serverless que recolecta, procesa y almacena automáticamente noticias sobre temas espoecíficos de salud.
2.  Una **API REST** que expone estos datos para ser consumidos por un **dashboard interactivo** desplegado en la nube.

<img width="1788" height="376" alt="image" src="https://github.com/user-attachments/assets/f6911cfa-93c7-40bc-bf02-be18a9e4ba31" />

---

## Fases del Proyecto

### Fase 1: Pipeline de Recolección de Datos

#### Características
* **Recolección Diaria Automatizada:** Se ejecuta cada día para buscar las noticias más recientes de tres APIs diferentes usando sus tiers gratuitos `GNews`, `NewsAPI`, `Newsdata.io`.
* **Procesamiento y Estandarización:** Limpia, unifica el formato y elimina artículos duplicados para asegurar la calidad de los datos.
* **Almacenamiento Persistente y Seguro:** Guarda los artículos en una base de datos **PostgreSQL (Amazon RDS)** dentro de una red privada.
* **Alertas por Correo Electrónico:** Envía un resumen diario por **Amazon SES** con los artículos nuevos que se han encontrado.
* **Arquitectura Segura:** Todos los componentes operan dentro de una **VPC**, y las credenciales se gestionan con **Secrets Manager** y **Parameter Store**.

#### Arquitectura del Pipeline
El pipeline sigue un flujo de datos claro y orquestado por servicios de AWS:
1.  **Disparador:** Cada día, **Amazon EventBridge** activa la función Lambda de recolección.
2.  **Ejecución:** Una **AWS Lambda** se inicia en la VPC, obtiene sus configuraciones y claves de API desde **Parameter Store**.
3.  **Conexión Externa:** Utiliza un **NAT Gateway** para conectarse de forma segura a las APIs de noticias en internet.
4.  **Almacenamiento:** La Lambda obtiene las credenciales de la base de datos desde **AWS Secrets Manager** y guarda los artículos nuevos en **Amazon RDS**.
5.  **Alerta:** Si se guardaron artículos nuevos, la Lambda usa **Amazon SES** para enviar un correo de resumen.

### Fase 2: API REST y Dashboard de Visualización

#### Características
* **API Serverless:** Una **API REST** construida con **Amazon API Gateway** y **AWS Lambda** que sirve los datos almacenados.
* **Endpoint Público:** Provee una URL pública y segura para consultar los datos de la base de datos en formato JSON.
* **Dashboard Interactivo:** Una aplicación web construida y desplegada con **Streamlit** que consume los datos de la API.
* **Visualización:** Permite a los usuarios visualizar las noticias y filtrarlas.

#### Arquitectura de la API y el Dashboard
1.  **Petición del Usuario:** Un usuario abre el dashboard desplegado en **Render**.
2.  **Llamada a la API:** El dashboard hecho en **Streamlit** realiza una petición HTTP a la URL de **Amazon API Gateway**.
3.  **Ejecución del Backend:** API Gateway redirige la petición a una segunda **AWS Lambda** (`news-api-handler`).
4.  **Consulta de Datos:** Esta Lambda, operando en la misma VPC, se conecta de forma segura a **Amazon RDS**, ejecuta una consulta `SELECT` para obtener las noticias y las devuelve en formato JSON.
5.  **Visualización:** El dashboard recibe el JSON y renderiza las noticias en una interfaz interactiva.

---

##  Herramientas y Servicios de AWS

* **Cómputo:** AWS Lambda
* **Base de Datos:** Amazon RDS (PostgreSQL)
* **Redes y Seguridad:** Amazon VPC, NAT Gateway, Internet Gateway, Security Groups, IAM
* **Integración y Orquestación:** Amazon EventBridge, Amazon API Gateway
* **Gestión de Configuración:** AWS Systems Manager Parameter Store, AWS Secrets Manager
* **Notificaciones:** Amazon SES
* **Dashboard:** Streamlit

---

## Estructura del Repositorio

Este repositorio contiene el código para el **dashboard de Streamlit**. El código para las funciones Lambda se gestiona por separado.

* **`app.py`**: Script principal de la aplicación Streamlit que construye la interfaz del dashboard y llama a la API.
* **`requirements.txt`**: Lista de las dependencias de Python necesarias para ejecutar el dashboard.
* **`README.md`**: Documentación completa del proyecto.
* **`img/`**: Carpeta que contiene las imágenes y diagramas utilizados en la documentación.

---

## Despliegue

El despliegue se divide en dos partes: el backend en AWS y el frontend en Render.

#### 1. Backend en AWS
* **Configuración Inicial:** Crear los parámetros en Parameter Store, los secretos en Secrets Manager, verificar la identidad en SES, y configurar la base de datos RDS y la red VPC.
* **Despliegue de Lambdas:** Empaquetar y desplegar las dos funciones Lambda (`news-collector` y `news-api-handler`), asignando los roles y capas necesarios.
* **Creación de la API:** Configurar el endpoint en API Gateway y conectarlo a la Lambda `news-api-handler`.
* **Configuración del Disparador:** Crear la regla en EventBridge para la ejecución diaria.

#### 2. Frontend en Streamlit
* Subir el código del dashboard a un repositorio de GitHub.
* Crear una nueva 'app' en Streamlit, conectándolo al repositorio.

---

## Resultado 

1.  Una **base de datos** que se actualiza diariamente con noticias sobre temas de salud, lista para ser utilizada en proyectos de análisis, visualización o data science.
2.  Un **correo electrónico de alerta** que se envía al usuario cada día que se encuentran noticias nuevas, proporcionando un resumen inmediato y accesible.
3.  Una **API REST** pública que expone los datos recolectados, permitiendo que aplicaciones externas, como el dashboard, puedan consumir la información de forma segura y escalable.


### *Vista de base de datos con artículos extraidos con SQL en DBeaver*
<img width="2525" height="1231" alt="image" src="https://github.com/user-attachments/assets/528321c0-4df8-4dd5-9012-6a3fb82c034c" />


### *Mapa de Recursos de la Virtual Private Cloud (VPC)*
<img width="1338" height="577" alt="image" src="https://github.com/user-attachments/assets/4ec299bb-ffbb-48bf-b8f4-66f23eea392e" />

### *Registro de prueba exitosa de la función Lambda*
<img width="1607" height="811" alt="image" src="https://github.com/user-attachments/assets/ea8cb716-9a3c-4c6c-82c6-e8cecfea7827" />

### *Correo de alerta diaria*
<img width="2213" height="1145" alt="image" src="https://github.com/user-attachments/assets/60e56278-f8a0-4fff-8431-d42536c506de" />

---

## Autor

**Ricardo Urdaneta**

**[LinkedIn](https://www.linkedin.com/in/ricardourdanetacastro)**
