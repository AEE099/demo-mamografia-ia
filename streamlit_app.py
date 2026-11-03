"""
streamlit_app.py — Demo educativo: una IA que lee mamografías (CMMD, datos abiertos).

La app no ejecuta el modelo: muestra las predicciones y mapas de calor (Grad-CAM) ya calculados
sobre la prueba sellada (163 mamas que el modelo nunca vio), así funciona rápido en cualquier equipo.

Ejecutar:
    pip install -r requirements.txt
    streamlit run streamlit_app.py
"""
import json
import random
import zipfile
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

AQUI = Path(__file__).parent
DATOS = AQUI / "datos" if (AQUI / "datos").exists() else AQUI   # funciona aunque la carpeta se aplane al subirla
IMAGENES_ZIP = DATOS / "imagenes.zip"   # las 652 imágenes en un solo archivo

CLARO = {"tinta": "#14212B", "tinta2": "#4E5D68", "linea": "#D6DEE3", "acento": "#0F7C8C",
         "fondo": "#F5F7F8", "superficie": "#E6EDF0", "naranja": "#B4561F", "azul": "#3D6FB6"}
OSCURO = {"tinta": "#E6EDF1", "tinta2": "#A3B1BA", "linea": "#2A3842", "acento": "#3FB8C6",
          "fondo": "#0F171D", "superficie": "#1B2830", "naranja": "#E08A55", "azul": "#7FA6E0"}
FUENTE_TXT = "Atkinson Hyperlegible"

FILTROS = {
    "Todos los casos": None,
    "Malignos detectados": "VP",
    "Malignos que se le escaparon": "FN",
    "Falsas alarmas (eran benignos)": "FP",
    "Benignos descartados": "VN",
}
RESULTADO = {
    "VP": ("✔", "Acierto: detectó un maligno"),
    "FN": ("✘", "Se le escapó un maligno"),
    "FP": ("✘", "Falsa alarma: era benigno"),
    "VN": ("✔", "Acierto: descartó un benigno"),
}
LADO = {"L": "mama izquierda", "R": "mama derecha"}


@st.cache_resource
def archivo_imagenes():
    return zipfile.ZipFile(IMAGENES_ZIP)


def imagen(nombre):
    return archivo_imagenes().read(f"imagenes/{nombre}")


@st.cache_data
def cargar():
    casos = pd.read_csv(DATOS / "casos.csv")
    res = json.loads((DATOS / "resultados_prueba.json").read_text(encoding="utf-8"))
    umbral = json.loads((DATOS / "umbral.json").read_text(encoding="utf-8"))["umbral_sens90"]
    vindr = json.loads((DATOS / "vindr_pointing.json").read_text(encoding="utf-8"))
    return casos, res, umbral, vindr


st.set_page_config(page_title="IA que lee mamografías", page_icon="🩻", layout="wide")
casos, RES, UMBRAL, VINDR = cargar()

cab, interruptor = st.columns([6, 1])
oscuro = interruptor.toggle("Modo oscuro", value=False)
P = OSCURO if oscuro else CLARO
TINTA, TINTA_2, LINEA, ACENTO, FONDO = P["tinta"], P["tinta2"], P["linea"], P["acento"], P["fondo"]
SUPERFICIE, NARANJA, AZUL = P["superficie"], P["naranja"], P["azul"]

# =============================================================================
# Estilo
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, button, input, label, table, [data-testid="stMetric"] {{
  font-family: '{FUENTE_TXT}', system-ui, sans-serif !important;
}}
.block-container {{ max-width: 1180px; padding-top: 4.5rem !important; }}
#MainMenu, footer {{ visibility: hidden; }}
.stApp, [data-testid="stAppViewContainer"], header[data-testid="stHeader"] {{ background: {FONDO} !important; }}
[data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
.stRadio label p {{ color: {TINTA} !important; }}
.stApp p.titulo {{ font-size: clamp(2.1rem, 3.8vw, 2.9rem) !important; line-height: 1.1 !important;
  font-weight: 700 !important; color: {TINTA} !important; letter-spacing: -0.015em; margin: 0 0 .5rem 0 !important; }}
.stApp p.subtitulo {{ font-size: 1.05rem !important; color: {TINTA_2} !important; margin: 0 0 1.2rem 0 !important;
  max-width: 78ch; line-height: 1.55 !important; }}
.stApp p.seccion {{ font-size: 1.55rem !important; font-weight: 700 !important; color: {TINTA} !important;
  margin: 2.6rem 0 .3rem 0 !important; }}
.stApp p.nota {{ font-size: .95rem !important; line-height: 1.55 !important; color: {TINTA_2} !important; max-width: 72ch; }}
.stApp p.pie {{ font-size: .85rem !important; color: {TINTA_2} !important; border-top: 1px solid {LINEA};
  padding-top: .8rem; margin-top: 2.5rem !important; line-height: 1.6 !important; }}
.vista {{ font-size: .85rem; color: {TINTA_2}; margin: .2rem 0 0 0; }}
.ficha {{ border-left: 4px solid {ACENTO}; padding: .2rem 0 .2rem 1.1rem; }}
.ficha .rotulo {{ font-size: .9rem; color: {TINTA_2}; margin: 0; }}
.ficha .prob {{ font-size: 3.2rem; font-weight: 700; color: {TINTA}; line-height: 1; margin: .2rem 0 .5rem 0; }}
.barra {{ position: relative; height: 12px; background: {SUPERFICIE}; border-radius: 6px; margin: .2rem 0 .3rem 0; }}
.barra .lleno {{ position: absolute; left: 0; top: 0; bottom: 0; background: {ACENTO}; border-radius: 6px; }}
.barra .corte {{ position: absolute; top: -5px; bottom: -5px; width: 2px; background: {TINTA}; }}
.ficha .eje {{ font-size: .8rem; color: {TINTA_2}; margin: 0 0 1rem 0; }}
.ficha .dato {{ font-size: 1.05rem; color: {TINTA}; margin: .35rem 0; line-height: 1.45; }}
.ficha .dato b {{ font-weight: 700; }}
.ficha .resultado {{ font-size: 1.15rem; font-weight: 700; margin: .9rem 0 .2rem 0; color: {TINTA}; }}
.ficha .oculto {{ font-size: 1.05rem; color: {TINTA_2}; font-style: italic; margin: .6rem 0; }}
.tarjetas {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1.2rem; margin: 1rem 0 .4rem 0; }}
.tarjeta {{ border-top: 3px solid {ACENTO}; padding-top: .6rem; }}
.tarjeta .grande {{ font-size: 2.3rem; font-weight: 700; color: {TINTA}; line-height: 1.05; }}
.tarjeta .chica {{ font-size: .98rem; color: {TINTA_2}; line-height: 1.45; margin-top: .3rem; }}
div[data-baseweb="select"] > div {{ background-color: {SUPERFICIE} !important; border-color: {LINEA} !important; }}
div[data-baseweb="select"] * {{ color: {TINTA} !important; fill: {TINTA} !important; }}
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li {{ background: {SUPERFICIE} !important; color: {TINTA} !important; }}
[data-testid="stExpander"] details {{ background: {FONDO} !important; border-color: {LINEA} !important; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{ color: {TINTA} !important; fill: {TINTA} !important; }}
.stButton button {{ background: {SUPERFICIE} !important; color: {TINTA} !important; border-color: {LINEA} !important; }}
.stButton button p {{ color: {TINTA} !important; }}
</style>
""", unsafe_allow_html=True)


def grafico_base(chart):
    return chart.configure(font=FUENTE_TXT, background=FONDO) \
        .configure_view(strokeWidth=0) \
        .configure_axis(labelColor=TINTA_2, titleColor=TINTA_2, gridColor=LINEA, domain=False,
                        tickColor=LINEA, labelFontSize=12, titleFontSize=12) \
        .configure_legend(labelColor=TINTA, labelFontSize=12, orient="top", title=None)


def pct(x):
    return f"{x * 100:.0f}%"


# =============================================================================
# Encabezado
# =============================================================================
cab.markdown(
    '<p class="titulo">Una IA que lee mamografías</p>'
    '<p class="subtitulo">Una red neuronal entrenada con mamografías públicas, confirmadas por biopsia, decide si un '
    'hallazgo parece benigno o maligno y muestra en qué parte de la imagen se fijó. Aquí ves cómo le fue con '
    f'{len(casos)} mamas que nunca había visto. Demo educativo: no es una herramienta clínica.</p>',
    unsafe_allow_html=True)

# =============================================================================
# 1. Explorar un caso
# =============================================================================
st.markdown('<p class="seccion">Mira un caso</p>', unsafe_allow_html=True)

if "caso" not in st.session_state:
    st.session_state.caso = int(casos.index[casos.resultado == "VP"][0])
    st.session_state.revelado = False

c1, c2, c3 = st.columns([3, 2, 1.4])
adivinar = c2.toggle("Modo adivinanza", value=False,
                     help="Oculta el diagnóstico y la respuesta de la IA hasta que pulses «Revelar».")
filtro = c1.selectbox("Tipo de caso", list(FILTROS), disabled=adivinar,
                      help="En modo adivinanza se muestran casos al azar sin filtrar.")
codigo = None if adivinar else FILTROS[filtro]
disponibles = casos.index[casos.resultado == codigo].tolist() if codigo else casos.index.tolist()

if c3.button("Otro caso", use_container_width=True):
    opciones = [i for i in disponibles if i != st.session_state.caso] or disponibles
    st.session_state.caso = random.choice(opciones)
    st.session_state.revelado = False
if st.session_state.caso not in disponibles:
    st.session_state.caso = disponibles[0]
    st.session_state.revelado = False

caso = casos.loc[st.session_state.caso]
mostrar = (not adivinar) or st.session_state.revelado
ver_mapa = st.toggle("Ver dónde mira la IA (mapa de calor)", value=mostrar, disabled=not mostrar)

v1, v2, info = st.columns([1, 1, 1.5], gap="large")
for col, vista, nombre in [(v1, caso.vista1, "Vista 1"), (v2, caso.vista2, "Vista 2")]:
    if isinstance(vista, str) and vista:
        sufijo = "cam" if (ver_mapa and mostrar) else "orig"
        col.image(imagen(f"{vista}_{sufijo}.jpg"), use_container_width=True)
        col.markdown(f'<p class="vista">{nombre} · {LADO.get(caso.lado, caso.lado)}</p>', unsafe_allow_html=True)

with info:
    detalle = (f'<p class="dato">Hallazgo: <b>{caso.tipo}</b> · Paciente de <b>{int(caso.edad)} años</b></p>')
    if mostrar:
        p = float(caso.probabilidad)
        icono, texto = RESULTADO[caso.resultado]
        decision = "Sospechoso de maligno" if caso.prediccion == "Maligno" else "Probablemente benigno"
        html = (f'<div class="ficha"><p class="rotulo">Probabilidad de maligno según la IA</p>'
                f'<p class="prob">{pct(p)}</p>'
                f'<div class="barra"><div class="lleno" style="width:{p*100:.1f}%"></div>'
                f'<div class="corte" style="left:{UMBRAL*100:.1f}%"></div></div>'
                f'<p class="eje">La línea marca el umbral: desde {pct(UMBRAL)} la IA lo considera sospechoso.</p>'
                f'<p class="dato">La IA dice: <b>{decision}</b></p>'
                f'<p class="dato">La biopsia dijo: <b>{caso.real}</b></p>'
                f'{detalle}'
                f'<p class="resultado">{icono} {texto}</p></div>')
    else:
        html = (f'<div class="ficha"><p class="rotulo">¿Qué opinas tú?</p>'
                f'<p class="oculto">Observa las dos vistas y decide si te parece benigno o maligno. '
                f'Luego compara con la IA y con la biopsia.</p>{detalle}</div>')
    st.markdown(html, unsafe_allow_html=True)
    if adivinar and not st.session_state.revelado:
        if st.button("Revelar", use_container_width=True):
            st.session_state.revelado = True
            st.rerun()

st.markdown('<p class="nota">Todas las mamas se muestran con la pared torácica a la izquierda. En el mapa de calor, '
            'el rojo marca las zonas que más empujaron a la IA hacia «maligno».</p>', unsafe_allow_html=True)

# =============================================================================
# 2. Qué tan bien funciona
# =============================================================================
st.markdown('<p class="seccion">¿Qué tan bien funciona?</p>', unsafe_allow_html=True)
cf = RES["confusion_umbral90"]
mal, ben = cf["tp"] + cf["fn"], cf["tn"] + cf["fp"]
st.markdown(f"""
<div class="tarjetas">
  <div class="tarjeta"><div class="grande">{cf['tp']} de {mal}</div>
    <div class="chica">malignos detectados ({pct(cf['tp']/mal)}). Se le escaparon {cf['fn']}.</div></div>
  <div class="tarjeta"><div class="grande">{cf['tn']} de {ben}</div>
    <div class="chica">benignos descartados ({pct(cf['tn']/ben)}). Los otros {cf['fp']} fueron falsas alarmas.</div></div>
  <div class="tarjeta"><div class="grande">{RES['auc']:.2f}</div>
    <div class="chica">AUC: capacidad de separar benignos de malignos (1 sería perfecta, 0.5 sería azar).
    Margen probable: {RES['ic95'][0]:.2f} a {RES['ic95'][1]:.2f}.</div></div>
  <div class="tarjeta"><div class="grande">{RES['auc_edad']:.2f}</div>
    <div class="chica">AUC usando solo la edad de la paciente. La IA ve algo en la imagen que la edad no explica.</div></div>
</div>
""", unsafe_allow_html=True)
st.markdown(f'<p class="nota">El umbral se fijó para <b>no dejar pasar malignos</b>, aunque eso genere más falsas '
            f'alarmas: un cáncer no detectado es más grave que un estudio adicional. Se decidió antes de evaluar '
            f'estas {len(casos)} mamas, que el modelo nunca había visto.</p>', unsafe_allow_html=True)

d = casos.assign(Biopsia=casos.real, Probabilidad=casos.probabilidad)
d["fila"] = d.groupby("Biopsia").cumcount() % 12
puntos = alt.Chart(d).mark_point(size=70, filled=True, opacity=0.85).encode(
    x=alt.X("Probabilidad:Q", title="Probabilidad de maligno según la IA", scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(format="%")),
    y=alt.Y("Biopsia:N", title=None, sort=["Maligno", "Benigno"]),
    yOffset=alt.YOffset("fila:O"),
    color=alt.Color("Biopsia:N", scale=alt.Scale(domain=["Maligno", "Benigno"], range=[NARANJA, AZUL])),
    shape=alt.Shape("Biopsia:N", scale=alt.Scale(domain=["Maligno", "Benigno"], range=["diamond", "circle"])),
    tooltip=[alt.Tooltip("PatientID:N", title="Caso"), alt.Tooltip("Biopsia:N"),
             alt.Tooltip("Probabilidad:Q", format=".0%"), alt.Tooltip("tipo:N", title="Hallazgo")])
corte = alt.Chart(pd.DataFrame({"x": [UMBRAL]})).mark_rule(color=TINTA, strokeDash=[4, 3]).encode(x="x:Q")
st.altair_chart(grafico_base((corte + puntos).properties(height=230)), use_container_width=True)
st.markdown('<p class="nota">Cada punto es una mama. A la derecha de la línea, la IA la marca como sospechosa. '
            'Los malignos (rombos) tienden a quedar a la derecha y los benignos (círculos) se reparten más: '
            'por eso hay tantas falsas alarmas.</p>', unsafe_allow_html=True)

# =============================================================================
# 3. ¿Mira donde debe?
# =============================================================================
st.markdown('<p class="seccion">¿Mira donde debe?</p>', unsafe_allow_html=True)
st.markdown('<p class="nota">A la IA nunca se le dijo dónde estaban las lesiones, solo si cada mama era benigna o '
            'maligna. Para comprobar si de todos modos aprendió a localizarlas, la probamos con <b>VinDr-Mammo</b>, '
            'mamografías de otro país en las que radiólogos marcaron cada hallazgo con un recuadro. Medimos cuántas '
            'veces el punto más caliente del mapa cae dentro del recuadro, y cuántas veces se acertaría '
            'señalando al azar dentro de la mama.</p>', unsafe_allow_html=True)

g = pd.DataFrame(VINDR["grupos"])
largo = g.melt(id_vars=["grupo", "n", "ic_inf", "ic_sup"], value_vars=["acierto", "azar"],
               var_name="serie", value_name="valor")
largo["serie"] = largo.serie.map({"acierto": "La IA señala la lesión", "azar": "Señalando al azar"})
orden = g.grupo.tolist()
barras = alt.Chart(largo).mark_bar(cornerRadiusEnd=4).encode(
    y=alt.Y("grupo:N", title=None, sort=orden),
    yOffset=alt.YOffset("serie:N", sort=["La IA señala la lesión", "Señalando al azar"]),
    x=alt.X("valor:Q", title="Imágenes en que el punto señalado cae dentro de la lesión (%)",
            scale=alt.Scale(domain=[0, 100])),
    color=alt.Color("serie:N", scale=alt.Scale(domain=["La IA señala la lesión", "Señalando al azar"],
                                               range=[ACENTO, LINEA])),
    tooltip=[alt.Tooltip("grupo:N", title="Grupo"), alt.Tooltip("serie:N", title=" "),
             alt.Tooltip("valor:Q", title="%", format=".0f"), alt.Tooltip("n:Q", title="Imágenes")])
etiquetas = alt.Chart(largo[largo.serie == "La IA señala la lesión"]).mark_text(
    align="left", dx=6, color=TINTA, fontSize=12).encode(
    y=alt.Y("grupo:N", sort=orden), yOffset=alt.YOffset("serie:N", sort=["La IA señala la lesión", "Señalando al azar"]),
    x="valor:Q", text=alt.Text("valor:Q", format=".0f"))
st.altair_chart(grafico_base((barras + etiquetas).properties(height=320)), use_container_width=True)
todas = g[g.grupo == "Todas"].iloc[0]
st.markdown(f'<p class="nota">En {int(todas.n)} imágenes con hallazgos sospechosos (BI-RADS 4 y 5), la IA señaló la '
            f'lesión en el <b>{todas.acierto:.0f}%</b> de los casos (margen probable {int(todas.ic_inf)}–{int(todas.ic_sup)}%), '
            f'frente a un {todas.azar:.0f}% al azar: unas {todas.acierto/todas.azar:.0f} veces más. Las imágenes de '
            f'VinDr no se muestran porque su licencia no permite redistribuirlas.</p>', unsafe_allow_html=True)

# =============================================================================
# 4. Lo que no hace
# =============================================================================
st.markdown('<p class="seccion">Lo que esta IA no hace</p>', unsafe_allow_html=True)
st.markdown(f"""
- **No hace tamizaje.** Se entrenó con hallazgos que ya eran sospechosos; no sabe buscar un cáncer en una mamografía normal.
- **No reemplaza la biopsia ni al radiólogo.** Se le escaparon {cf['fn']} de {mal} malignos, casi todos masas en mamas densas.
- **No viaja sin ajustes.** En las mamografías de VinDr, de otro país y otros equipos, sus probabilidades subieron en
  general (las normales recibieron en promedio {VINDR['probabilidad_media_normales']:.0%}). Un modelo así debe validarse
  y recalibrarse con los datos de cada servicio antes de usarse.
- **Aprendió de una población específica:** mujeres atendidas en China. Su desempeño en otras poblaciones no está demostrado.
""")

with st.expander("Cómo se construyó"):
    st.markdown("""
- **Datos:** 1,107 mamas de *The Chinese Mammography Database* (CMMD), con diagnóstico confirmado por biopsia.
  Se usó solo el grupo con casos benignos y malignos del mismo origen, para evitar atajos.
- **División por paciente:** 70% para aprender, 15% para ajustar decisiones y 15% guardado como prueba final.
  Ninguna paciente aparece en dos grupos.
- **Modelo:** tres redes EfficientNet-B0 preentrenadas, ajustadas a imágenes de 1024 píxeles de alto, cuyas
  predicciones se promedian. Se combatió el sobreajuste con regularización y aumentos de datos.
- **Umbral:** fijado con el grupo de ajuste para detectar al menos el 90% de los malignos, antes de abrir la prueba.
- **Mapas de calor:** Grad-CAM, que indica qué regiones de la imagen pesaron más en la decisión.
""")

st.markdown(
    '<p class="pie">Imágenes: The Chinese Mammography Database (CMMD), The Cancer Imaging Archive, '
    'DOI 10.7937/tcia.eqde-4b16, licencia CC BY 4.0; recortadas, reducidas y con mapas Grad-CAM superpuestos. '
    'Prueba de localización: VinDr-Mammo (PhysioNet), solo resultados agregados. '
    'Demo educativo elaborado por Alonzo Encarnación. No es un dispositivo médico ni sustituye el criterio clínico.</p>',
    unsafe_allow_html=True)
