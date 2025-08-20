import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import re
from html import unescape

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard de Noticias de Salud",
    page_icon="📰",
    layout="wide"
)

# --- API URL ---
API_URL = "https://v1ctjeryd0.execute-api.us-east-1.amazonaws.com/prod/noticias"

# --- Autor y Enlaces ---
autor = "Ricardo Urdaneta"
linkedin_url = "https://www.linkedin.com/in/ricardourdanetacastro"
github_url = "https://github.com/Ricardouchub"

# --- Estilo ---
st.markdown("""
<style>
section[data-testid="stSidebar"]{
  min-width:250px !important; max-width:250px !important;
}
.block-container{ padding-top:1.2rem; padding-bottom:2rem; }
</style>
""", unsafe_allow_html=True)

# --- Barra Lateral ---
with st.sidebar:
    st.header("Filtrado y Visualización")
    num_noticias = st.radio("Mostrar por página:", [10, 20, 30], index=0, horizontal=True)

    st.subheader("Filtrar por Fecha")
    fecha_inicio = st.date_input("Fecha de Inicio", value=pd.to_datetime('today') - pd.Timedelta(days=30))
    fecha_fin = st.date_input("Fecha de Fin", value=pd.to_datetime('today'))

    st.subheader("Búsqueda")
    q = st.text_input("Texto (título/descr.)", placeholder="dengue, OMS, vacuna...")

    st.divider()
    st.markdown("**Realizado por**")
    st.markdown(autor)
    st.markdown(f"[GitHub]({github_url}) · [LinkedIn]({linkedin_url})")

# --- Carga de datos ---
@st.cache_data(ttl=600)
def load_data():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        body = r.json().get("body")
        data = json.loads(body) if isinstance(body, str) else body
        df = pd.DataFrame(data)
        if df.empty:
            return df
        df['published_at'] = pd.to_datetime(
            df['published_at'], format='mixed', errors='coerce', utc=True
        ).dt.tz_localize(None)
        df.dropna(subset=['published_at'], inplace=True)
        for col in ['title','description','source','url','topic','country']:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df
    except Exception as e:
        st.error(f"Ocurrió un problema al cargar los datos: {e}")
        return pd.DataFrame()

# --- Utilidades ---
MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto",
            "septiembre","octubre","noviembre","diciembre"]
def fecha_es(dt: datetime) -> str:
    if pd.isna(dt): return "—"
    return f"{dt.day} de {MESES_ES[dt.month-1]}, {dt.year} - {dt:%H:%M} (UTC)"

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
def clean_html(text: str) -> str:
    """
    Limpia HTML de manera segura:
    - Convierte entidades (&nbsp; &amp; etc.)
    - Elimina etiquetas <...>
    - Normaliza espacios
    """
    if not text:
        return ""
    txt = unescape(text)
    txt = TAG_RE.sub(" ", txt)
    txt = WS_RE.sub(" ", txt).strip()
    return txt

# --- Header ---
st.markdown("# Monitoreo de Noticias de Enfermedades Virales")
st.caption("Este dashboard presenta un resumen de las últimas noticias sobre temas de salud referente a enfermedades virales (virus, brotes, pandemias, etc.). Los datos son recolectados automáticamente a través de un pipeline de datos construido en AWS, que extrae información de diversas fuentes de noticias, la procesa, almacena y finalmente la expone a través de una API. Este dashboard consulta dicha API para mostrar las noticias más recientes, permitiendo filtrar la cantidad de artículos mostrados y el rango de fechas de publicación..")
st.markdown("---")

# --- Datos ---
data_df = load_data()

if data_df.empty:
    st.warning("No se pudieron cargar los datos o no hay artículos disponibles.")
else:
    # Filtrado
    df = data_df.copy()
    df = df[(df['published_at'].dt.date >= fecha_inicio) & (df['published_at'].dt.date <= fecha_fin)]
    if q:
        q_low = q.lower()
        df = df[
            df['title'].str.lower().str.contains(q_low) |
            df['description'].str.lower().str.contains(q_low)
        ]

    # KPIs
    total_periodo = len(df)
    total_fuentes = df['source'].nunique() if 'source' in df.columns else 0
    fecha_min, fecha_max = df['published_at'].min(), df['published_at'].max()
    c1, c2, c3 = st.columns(3)
    c1.metric("Artículos", f"{total_periodo}")
    c2.metric("Fuentes únicas", f"{total_fuentes}")
    if pd.notnull(fecha_min) and pd.notnull(fecha_max):
        c3.metric("Ventana temporal", f"{fecha_es(fecha_min)} — {fecha_es(fecha_max)}")

    st.markdown("---")

    # Orden + paginación
    df.sort_values(by='published_at', ascending=False, inplace=True)
    page_size = int(num_noticias)
    total_pages = max(1, (len(df) + page_size - 1) // page_size)
    cols_p = st.columns([1,6,2])
    with cols_p[0]:
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1)
    with cols_p[-1]:
        st.write(f"Total: **{len(df)}** artículos")

    start, end = (page - 1) * page_size, (page - 1) * page_size + page_size
    page_df = df.iloc[start:end].copy()

    # Render de tarjetas
    if page_df.empty:
        st.info("No se encontraron noticias con los filtros seleccionados.")
    else:
        for _, row in page_df.iterrows():
            title = clean_html(row.get('title', 'Sin título'))
            url = row.get('url', '#')
            src = clean_html(row.get('source', '—'))
            desc = clean_html(row.get('description', ''))
            ts = row.get('published_at', None)
            topic = clean_html(row.get('topic', '')) if 'topic' in row else ''
            country = clean_html(row.get('country', '')) if 'country' in row else ''

            with st.container(border=True):
                # título con link
                st.markdown(f"### [{title}]({url})")
                # metadatos
                meta = " · ".join([x for x in [src, topic or None, country or None] if x]) or "—"
                st.caption(f"{meta} · Publicado: {fecha_es(ts)}")
                # descripción plana
                if desc:
                    st.write(desc)

    st.markdown("---")
    st.caption("Fuente de datos: API en AWS · Construido con Streamlit")