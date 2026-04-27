import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Simulador NNN Escolar", layout="wide", page_icon="🩺")

# 2. ESTILOS PERSONALIZADOS (Opcional para que se vea mejor)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. TÍTULO Y GUÍA DE USO
st.title("🩺 Gestor de Planes de Cuidado NNN")

with st.expander("📖 Guía rápida de uso (Leer antes de empezar)"):
    st.markdown("""
    1. **Sube tu Excel** en la barra lateral (o usa el de ejemplo).
    2. **Selecciona un Diagnóstico NANDA** para activar el proceso.
    3. **Elige Intervenciones (NIC)** y **Resultados (NOC)** sugeridos.
    4. **Evalúa Indicadores:** Al elegir un NOC, abre su sección y califica del 1 al 5.
    5. **Finaliza:** Genera el resumen y descárgalo para tu entrega.
    """)

# 4. FUNCIÓN DE CARGA DE DATOS
@st.cache_data
def cargar_datos(file):
    try:
        nanda = pd.read_excel(file, sheet_name='NANDA')
        noc = pd.read_excel(file, sheet_name='NOC')
        nic = pd.read_excel(file, sheet_name='NIC')
        vinculos = pd.read_excel(file, sheet_name='VINCULOS')
        indicadores = pd.read_excel(file, sheet_name='INDICADORES')
        
        # Normalización de IDs a Texto para evitar errores de coincidencia
        for df in [nanda, noc, nic, vinculos, indicadores]:
            for col in df.columns:
                if 'ID' in col:
                    df[col] = df[col].astype(str).str.strip()
        return nanda, noc, nic, vinculos, indicadores
    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")
        return None

# 5. BARRA LATERAL PARA CARGA DE ARCHIVOS
with st.sidebar:
    st.header("⚙️ Configuración")
    archivo_subido = st.file_uploader("Carga tu archivo Excel NNN", type=["xlsx"])
    
    # Intentar cargar archivo subido o el local por defecto
    archivo_a_usar = archivo_subido if archivo_subido else 'datos_enfermeria.xlsx'
    
    try:
        df_nanda, df_noc, df_nic, df_vinculos, df_indicadores = cargar_datos(archivo_a_usar)
        st.success("Base de datos lista")
    except:
        st.warning("⚠️ Esperando archivo 'datos_enfermeria.xlsx' o carga manual.")
        st.stop()

# 6. INTERFAZ PRINCIPAL (Solo si los datos cargaron bien)
if df_nanda is not None:
    
    # Selector NANDA con opción neutra
    opciones_nanda = ["Seleccione un diagnóstico..."] + sorted(list(df_nanda['Etiqueta'].unique()))
    nanda_sel = st.selectbox("Seleccione Diagnóstico NANDA:", opciones_nanda, index=0)

    if nanda_sel != "Seleccione un diagnóstico...":
        
        # Extraer info de NANDA
        fila_nanda = df_nanda[df_nanda['Etiqueta'] == nanda_sel]
        id_nanda = fila_nanda['ID_NANDA'].iloc[0]
        st.info(f"**Definición:** {fila_nanda['Definicion'].iloc[0]}")

        # Filtrado de Relaciones
        relaciones = df_vinculos[df_vinculos['ID_NANDA'] == id_nanda]
        
        st.markdown("---")
        col1, col2 = st.columns(2)

        # SECCIÓN NIC
        with col1:
            st.subheader("2. Intervenciones (NIC)")
            ids_nic = relaciones['ID_NIC'].unique()
            opciones_nic = df_nic[df_nic['ID_NIC'].isin(ids_nic)]
            nics_sel = st.multiselect("Seleccione las intervenciones sugeridas:", opciones_nic['Etiqueta'])

        # SECCIÓN NOC
        with col2:
            st.subheader("3. Resultados (NOC)")
            ids_noc = relaciones['ID_NOC'].unique()
            opciones_noc = df_noc[df_noc['ID_NOC'].isin(ids_noc)]
            nocs_sel = st.multiselect("Seleccione los resultados esperados:", opciones_noc['Etiqueta'])

        # EVALUACIÓN DE INDICADORES
        puntuaciones = {}
        if nocs_sel:
            st.markdown("### 📊 Evaluación de Indicadores (Escala Likert)")
            for n in nocs_sel:
                id_noc = df_noc.loc[df_noc['Etiqueta'] == n, 'ID_NOC'].iloc[0]
                inds = df_indicadores[df_indicadores['ID_NOC'] == id_noc]
                
                with st.expander(f"Indicadores de: {n}"):
                    if inds.empty:
                        st.write("No hay indicadores registrados para este resultado.")
                    else:
                        for idx, row in inds.iterrows():
                            # El key debe ser único para que Streamlit no se confunda
                            valor = st.select_slider(
                                f"{row['Indicador']}",
                                options=[1, 2, 3, 4, 5],
                                value=3,
                                key=f"ind_{idx}"
                            )
                            puntuaciones[f"{n} - {row['Indicador']}"] = valor

        # BOTÓN FINAL Y DESCARGA
        st.markdown("---")
        if st.button("Generar Plan de Cuidados Final"):
            if not nics_sel or not nocs_sel:
                st.warning("Selecciona al menos un NIC y un NOC para finalizar.")
            else:
                resumen = f"PLAN DE CUIDADOS ENFERMERÍA\n"
                resumen += f"{'='*30}\n\n"
                resumen += f"DIAGNÓSTICO NANDA: {nanda_sel}\n\n"
                resumen += f"INTERVENCIONES NIC:\n- " + "\n- ".join(nics_sel) + "\n\n"
                resumen += f"EVALUACIÓN DE INDICADORES NOC:\n"
                for k, v in puntuaciones.items():
                    resumen += f"- {k}: {v}/5\n"
                
                st.success("¡Plan generado correctamente!")
                st.text_area("Resultado (Copia y pega):", resumen, height=250)
                
                st.download_button(
                    label="📥 Descargar Plan en .txt",
                    data=resumen,
                    file_name=f"Plan_{nanda_sel[:20]}.txt",
                    mime="text/plain"
                )
    else:
        st.write("👈 Comienza seleccionando un diagnóstico arriba.")

# Footer
st.markdown("---")
st.caption("Herramienta Educativa PAE | NANDA-NOC-NIC")


