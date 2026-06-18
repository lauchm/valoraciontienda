import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
import io
import requests

# ============================================================
# CONFIGURACIÓN — PERSONALIZA AQUÍ TU MARCA
# ============================================================
EMPRESA = "TU TIENDA"                  # <-- Cambia esto por el nombre real de la empresa
LOGO_PATH = "logo.png"                 # <-- Pon tu logo (PNG/JPG) en esta misma carpeta con este nombre

COLOR_PRIMARIO = "#0F3D3E"             # Verde petróleo — color principal de marca
COLOR_SECUNDARIO = "#FF6B4A"           # Coral — color de acento
COLOR_FONDO = "#F7F5F1"                # Crema — fondo general
COLOR_TARJETA = "#FFFFFF"              # Blanco — fondo de tarjetas/botones
COLOR_TEXTO = "#1C1C1C"                # Texto principal

# --- Google Form (guardado) y Google Sheet (lectura de estadísticas) ---
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeewgmJlHEkir0rxbdutf9nlCKtg4pD4Wj3Iv_1GrKQlP9IDQ/formResponse"
ENTRY_ALBARAN = "entry.2037040514"
ENTRY_VALORACION = "entry.1051794112"
ENTRY_PUNTUACION = "entry.1166063584"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EMdjTo2PmVnJvkfyj78q0LjpmWzsKYJ4MZW64XyhOj8/gviz/tq?tqx=out:csv&gid=0"

# Contraseña de administrador.
# En local puedes dejarla aquí abajo (valor "1234" por defecto).
# Si despliegas en Streamlit Community Cloud, mejor defínela en "Secrets" (ver instrucciones aparte).
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    ADMIN_PASSWORD = "1234"

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title=f"Valoración — {EMPRESA}",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# ESTILOS
# ============================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

#MainMenu {{visibility:hidden;}}
footer {{visibility:hidden;}}
header {{visibility:hidden;}}

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background: {COLOR_FONDO};
}}

h1, h2, h3 {{
    font-family: 'Poppins', sans-serif;
    color: {COLOR_PRIMARIO};
}}

div.stButton > button {{
    height: 70px;
    width: 100%;
    font-size: 1.2rem;
    font-weight: 600;
    white-space: pre-line;
    line-height: 1.3;
    border-radius: 14px;
    border: 2px solid rgba(15,61,62,0.12);
    background-color: {COLOR_TARJETA};
    color: {COLOR_TEXTO};
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}}

div.stButton > button:hover {{
    border-color: {COLOR_SECUNDARIO};
    box-shadow: 0 6px 20px rgba(0,0,0,0.10);
}}

div.stButton > button:active {{
    transform: scale(0.97);
}}

div.stButton > button[kind="primary"] {{
    background-color: {COLOR_PRIMARIO} !important;
    color: white !important;
    border: none !important;
    height: 64px;
    font-size: 1.1rem;
}}

.logo-texto {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 2.1rem;
    color: {COLOR_PRIMARIO};
    letter-spacing: 1px;
    text-align: center;
}}

div[data-testid="stMetric"] {{
    background-color: {COLOR_TARJETA};
    border-radius: 14px;
    padding: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}

/* Campo de albarán — grande y táctil */
div[data-testid="stTextInput"] > div {{
    height: 80px;
    border-radius: 16px;
}}

div[data-testid="stTextInput"] input {{
    height: 100%;
    box-sizing: border-box;
    font-size: 1.8rem;
    text-align: center;
    line-height: normal;
    padding: 0 1rem;
    border-radius: 16px;
    border: 2px solid rgba(15,61,62,0.18);
    background-color: {COLOR_TARJETA};
}}

div[data-testid="stTextInput"] input::placeholder {{
    font-size: 1.3rem;
    color: #999;
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO DE SESIÓN
# ============================================================
if "pantalla" not in st.session_state:
    st.session_state.pantalla = 1
if "albaran" not in st.session_state:
    st.session_state.albaran = ""
if "albaran_actual" not in st.session_state:
    st.session_state.albaran_actual = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def mostrar_cabecera():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        else:
            st.markdown(f"<div class='logo-texto'>{EMPRESA}</div>", unsafe_allow_html=True)


def cara_svg(color_circulo, tipo):
    """Genera un icono de carita en SVG (vectorial, sin depender de archivos externos)."""
    if tipo == "muy_mala":
        boca = '<path d="M30,72 Q50,55 70,72" stroke="#1f1f1f" stroke-width="5" fill="none" stroke-linecap="round"/>'
        cejas = ('<line x1="24" y1="32" x2="40" y2="40" stroke="#1f1f1f" stroke-width="5" stroke-linecap="round"/>'
                  '<line x1="76" y1="32" x2="60" y2="40" stroke="#1f1f1f" stroke-width="5" stroke-linecap="round"/>')
    elif tipo == "mala":
        boca = '<path d="M32,70 Q50,58 68,70" stroke="#1f1f1f" stroke-width="5" fill="none" stroke-linecap="round"/>'
        cejas = ""
    elif tipo == "regular":
        boca = '<line x1="32" y1="68" x2="68" y2="68" stroke="#1f1f1f" stroke-width="5" stroke-linecap="round"/>'
        cejas = ""
    elif tipo == "buena":
        boca = '<path d="M32,60 Q50,75 68,60" stroke="#1f1f1f" stroke-width="5" fill="none" stroke-linecap="round"/>'
        cejas = ""
    else:  # excelente
        boca = '<path d="M26,56 Q50,84 74,56" stroke="#1f1f1f" stroke-width="6" fill="none" stroke-linecap="round"/>'
        cejas = ""

    # Todo en una sola línea: si quedara una línea vacía dentro del bloque,
    # Streamlit corta el HTML por la mitad y se ve el código como texto.
    svg = (
        '<svg viewBox="0 0 100 100" width="100%" style="max-width:120px;" xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="50" cy="50" r="46" fill="{color_circulo}" stroke="rgba(0,0,0,0.15)" stroke-width="2"/>'
        '<circle cx="35" cy="42" r="5.5" fill="#1f1f1f"/>'
        '<circle cx="65" cy="42" r="5.5" fill="#1f1f1f"/>'
        f'{cejas}{boca}'
        '</svg>'
    )
    return f'<div style="text-align:center; padding:0 8px;">{svg}</div>'


def guardar_valoracion(valoracion, puntuacion):
    datos = {
        ENTRY_ALBARAN: st.session_state.albaran_actual,
        ENTRY_VALORACION: valoracion,
        ENTRY_PUNTUACION: puntuacion,
    }
    try:
        requests.post(
            FORM_URL,
            data=datos,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
    except Exception:
        # Si falla el envío no bloqueamos al cliente; simplemente no queda registrada esta valoración.
        pass


def finalizar(valoracion, puntuacion):
    guardar_valoracion(valoracion, puntuacion)

    st.balloons()
    st.success("¡Gracias por su valoración!")

    time.sleep(2.5)

    st.session_state.albaran = ""
    st.session_state.albaran_actual = ""
    st.session_state.pantalla = 1
    st.rerun()


# ============================================================
# PANTALLAS — CLIENTE
# ============================================================
def pantalla_cliente_1():
    mostrar_cabecera()
    st.markdown(
        "<h2 style='text-align:center; margin-top:1.5rem;'>Introduzca su número de albarán</h2>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input(
            "Número de albarán",
            key="albaran",
            label_visibility="collapsed",
            placeholder="Ej: AL-2026-00123",
        )
        if st.button("Siguiente ➜", type="primary", use_container_width=True):
            valor = st.session_state.albaran.strip()
            if valor == "":
                st.warning("Por favor, introduce un número de albarán antes de continuar.")
            else:
                st.session_state.albaran_actual = valor
                st.session_state.pantalla = 2
                st.rerun()


def pantalla_cliente_2():
    mostrar_cabecera()
    st.markdown(
        "<h2 style='text-align:center; margin-top:1rem;'>¿Cómo ha sido su experiencia?</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    opciones = [
        ("#D32F2F", "muy_mala", "Muy mala", 1),
        ("#F57C00", "mala", "Mala", 2),
        ("#FBC02D", "regular", "Regular", 3),
        ("#9CCC65", "buena", "Buena", 4),
        ("#43A047", "excelente", "Excelente", 5),
    ]

    cols = st.columns(5)
    for col, (color, tipo, texto, puntos) in zip(cols, opciones):
        with col:
            st.markdown(cara_svg(color, tipo), unsafe_allow_html=True)
            if st.button(texto, key=f"btn_{puntos}", use_container_width=True):
                finalizar(texto, puntos)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("⟵ Volver", use_container_width=True):
            st.session_state.pantalla = 1
            st.rerun()


# ============================================================
# PANTALLAS — ADMINISTRADOR
# ============================================================
def pantalla_login_admin():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div class='logo-texto'>🔒 Acceso administrador</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        clave = st.text_input("Contraseña", type="password", label_visibility="collapsed", placeholder="Contraseña")
        if st.button("Entrar", type="primary", use_container_width=True):
            if clave == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")


def panel_admin():
    col_titulo, col_salir = st.columns([5, 1])
    with col_titulo:
        st.title("📊 Estadística")
    with col_salir:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cerrar sesión"):
            st.session_state.is_admin = False
            st.rerun()

    try:
        respuesta = requests.get(SHEET_CSV_URL, timeout=10)
        respuesta.raise_for_status()
        df = pd.read_csv(io.StringIO(respuesta.text))
    except Exception:
        st.error("No se han podido cargar los datos de la hoja. Comprueba que sigue compartida como 'Cualquier persona con el enlace'.")
        return

    if df.empty:
        st.info("Todavía no hay valoraciones registradas.")
        return

    # La primera columna la pone Google Forms automáticamente con la fecha de envío.
    df.columns = ["Fecha", "Albaran", "Valoracion", "Puntuacion"]
    df["Puntuacion"] = pd.to_numeric(df["Puntuacion"], errors="coerce")
    df = df.dropna(subset=["Puntuacion"])

    if df.empty:
        st.info("Todavía no hay valoraciones registradas.")
        return

    total = len(df)
    media = round(df["Puntuacion"].mean(), 2)
    satisfechos = round(len(df[df["Puntuacion"] >= 4]) / total * 100, 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("Valoraciones totales", total)
    c2.metric("Nota media", f"{media} / 5")
    c3.metric("% satisfechos", f"{satisfechos}%")

    st.subheader("Distribución de valoraciones")
    st.bar_chart(df["Valoracion"].value_counts())

    st.subheader("Valoraciones por día")
    df["Dia"] = pd.to_datetime(df["Fecha"]).dt.date
    st.line_chart(df.groupby("Dia").size())

    st.subheader("Buscar por número de albarán")
    buscar = st.text_input("Número de albarán", key="buscar_albaran")
    if buscar:
        st.dataframe(df[df["Albaran"].astype(str) == buscar], use_container_width=True)

    st.subheader("Últimas valoraciones")
    st.dataframe(df.tail(20), use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Valoraciones")

    st.download_button(
        "⬇️ Descargar Excel",
        data=buffer.getvalue(),
        file_name="valoraciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ============================================================
# ENRUTAMIENTO
# ============================================================
params = st.query_params
modo_admin = "admin" in params

if modo_admin:
    if st.session_state.is_admin:
        panel_admin()
    else:
        pantalla_login_admin()
else:
    if st.session_state.pantalla == 1:
        pantalla_cliente_1()
    elif st.session_state.pantalla == 2:
        pantalla_cliente_2()
