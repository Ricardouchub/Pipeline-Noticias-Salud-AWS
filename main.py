import os
import requests
import json
import boto3
import psycopg2 
from datetime import datetime

KEYWORDS = "virus OR gripe OR influenza OR epidemia OR brote"

# --- Obtiene toda la configuración de la aplicación desde Parameter Store ---
def get_app_config():
    """Obtiene todas las variables de configuración desde Parameter Store."""
    ssm = boto3.client('ssm')
    
    param_names = [
        '/news-project/gnews-key', 
        '/news-project/newsapi-key', 
        '/news-project/newsdata-key',
        '/news-project/recipient-email'
    ]
    
    try:
        response = ssm.get_parameters(Names=param_names, WithDecryption=True)
        
        config = {}
        for param in response['Parameters']:
            key_name = param['Name'].split('/')[-1] # ej: 'gnews-key'
            config[key_name] = param['Value']
            
        # Verifica que todos los parámetros necesarios fueron cargados
        if len(config) < len(param_names):
            print("Error: No se pudieron cargar todos los parámetros de configuración.")
            return None

        return config
    except Exception as e:
        print(f"Error al obtener configuración de Parameter Store: {e}")
        return None

# --- Obtiene las credenciales de la BD desde Secrets Manager ---
def get_db_credentials():
    """Obtiene las credenciales de la base de datos desde AWS Secrets Manager."""
    secrets_client = boto3.client('secretsmanager')
    secret_name = "news-project/database-credentials"
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret
    except Exception as e:
        print(f"Error al obtener credenciales de Secrets Manager: {e}")
        return None

# --- Estandariza el formato de los artículos ---
def standardize_article(article, source_api):
    """Unifica el formato de un artículo sin importar su origen."""
    try:
        if source_api == 'gnews':
            return {'title': article['title'], 'description': article.get('description', ''), 'url': article['url'], 'source': article['source']['name'], 'published_at': article['publishedAt']}
        elif source_api == 'newsapi':
            return {'title': article['title'], 'description': article.get('description', ''), 'url': article['url'], 'source': article['source']['name'], 'published_at': article['publishedAt']}
        elif source_api == 'newsdata':
            description = article.get('description') or article.get('content', '')
            return {'title': article['title'], 'description': description, 'url': article['link'], 'source': article.get('source_id', 'Unknown'), 'published_at': article['pubDate']}
    except KeyError as e:
        print(f"Artículo omitido por campo faltante: {e}")
        return None

# --- Funciones para buscar noticias en cada API ---
def fetch_gnews(api_key):
    print("Buscando en GNews...")
    url = f"https://gnews.io/api/v4/search?q={KEYWORDS}&lang=es&max=10&apikey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            return [standardize_article(a, 'gnews') for a in articles if a]
        else:
            print(f"Error en GNews: Código {response.status_code}. Respuesta: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión en GNews: {e}")
        return []

def fetch_newsapi(api_key):
    print("Buscando en NewsAPI...")
    url = f"https://newsapi.org/v2/everything?q={KEYWORDS}&language=es&pageSize=10&apiKey={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            return [standardize_article(a, 'newsapi') for a in articles if a]
        else:
            print(f"Error en NewsAPI: Código {response.status_code}. Respuesta: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión en NewsAPI: {e}")
        return []

def fetch_newsdata(api_key):
    print("Buscando en Newsdata.io...")
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={KEYWORDS}&language=es"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            articles = response.json().get('results', [])
            return [standardize_article(a, 'newsdata') for a in articles if a]
        else:
            print(f"Error en Newsdata.io: Código {response.status_code}. Respuesta: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión en Newsdata.io: {e}")
        return []

# --- Guarda artículos en la base de datos y devuelve los nuevos ---
def save_articles_to_db(credentials, articles):
    """Guarda artículos en RDS y devuelve una lista de los que se insertaron."""
    conn = None
    new_articles = []
    try:
        conn = psycopg2.connect(
            host=credentials['host'],
            dbname='postgres',
            user=credentials['username'],
            password=credentials['password'],
            port=credentials['port']
        )
        cursor = conn.cursor()
        
        # Este comando crea la tabla solo si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL UNIQUE,
                source TEXT,
                published_at TEXT,
                inserted_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        for article in articles:
            # Intentamos insertar y usamos RETURNING url para saber si la inserción fue exitosa
            cursor.execute(
                "INSERT INTO articles (title, description, url, source, published_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING RETURNING url",
                (article['title'], article['description'], article['url'], article['source'], article['published_at'])
            )
            inserted_url = cursor.fetchone()
            if inserted_url:
                new_articles.append(article)
        
        conn.commit()
        cursor.close()
        print(f"\nSe guardaron {len(new_articles)} artículos nuevos en la base de datos.")
        return new_articles
    except Exception as e:
        print(f"Error de base de datos: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

# --- Envía una alerta por correo electrónico con los nuevos artículos ---
def send_email_alert(new_articles, recipient_email):
    """Formatea y envía un correo con el resumen de noticias."""
    SENDER = recipient_email
    RECIPIENT = recipient_email
    
    ses_client = boto3.client('ses', region_name="us-east-1") # Asegúrate de que tu región sea correcta

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"Resumen de Noticias de Salud - {today}"
    
    html_body = f"""
    <html>
    <head>
        <style> body {{ font-family: sans-serif; }} </style>
    </head>
    <body>
      <h1>Resumen de Noticias de Salud</h1>
      <p>Se encontraron {len(new_articles)} artículos nuevos hoy:</p>
      <hr>
    """
    
    for article in new_articles:
        html_body += f"""
        <h2><a href="{article['url']}">{article['title']}</a></h2>
        <p><b>Fuente:</b> {article['source']}</p>
        <p>{article.get('description', 'No hay descripción disponible.')}</p>
        <br>
        """
    
    html_body += "</body></html>"

    try:
        response = ses_client.send_email(
            Destination={'ToAddresses': [RECIPIENT]},
            Message={
                'Body': {'Html': {'Charset': "UTF-8", 'Data': html_body}},
                'Subject': {'Charset': "UTF-8", 'Data': subject},
            },
            Source=SENDER,
        )
        print(f"Correo enviado exitosamente a {RECIPIENT}! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

# --- Punto de Entrada Principal de AWS Lambda ---
def lambda_handler(event, context):
    print(f"Iniciando recolección de noticias... {datetime.now()}")
    
    config = get_app_config()
    if not config:
        return {'statusCode': 500, 'body': json.dumps('Error: No se pudo cargar la configuración.')}

    recipient_email = config.get('recipient-email')
    
    all_articles = []
    all_articles.extend(fetch_gnews(config.get('gnews-key')))
    all_articles.extend(fetch_newsapi(config.get('newsapi-key')))
    all_articles.extend(fetch_newsdata(config.get('newsdata-key')))
    
    all_articles = [article for article in all_articles if article is not None]
    unique_articles = list({article['url']: article for article in all_articles}.values())
    
    print(f"Se encontraron {len(unique_articles)} artículos únicos.")
    
    db_credentials = get_db_credentials()
    if not db_credentials:
         return {'statusCode': 500, 'body': json.dumps('Error: No se pudo cargar las credenciales de la BD.')}

    if unique_articles:
        newly_added_articles = save_articles_to_db(db_credentials, unique_articles)
        
        if newly_added_articles and recipient_email:
            send_email_alert(newly_added_articles, recipient_email)
        elif not recipient_email:
            print("No se encontró email de destinatario en la configuración, no se enviará correo.")

    return {
        'statusCode': 200,
        'body': json.dumps(f'Proceso completado. Se encontraron {len(unique_articles)} artículos únicos.')
    }