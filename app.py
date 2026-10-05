import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="Resumen de Transacciones",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilo moderno (un poco de CSS para que se vea más lindo)
st.markdown("""
<style>
    .main { background-color: #fafafa; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #1f4e79; }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #666; }
    h1 { color: #1f4e79; }
    h2, h3 { color: #333; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 0 20px;
        background-color: #f0f2f6;
        border-radius: 8px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f4e79 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# MAPEO DE TERMINALES
# ============================================================
TERMINALES = {
    69510721: "CAPELLI CORDOBA FLEX",
    69510718: "CAPELLI CORDOBA MINI",
    69510722: "CAPELLI SANTIAGO",
    69510723: "CAPELLI ALVARADO",
    69510726: "IDRAET PRO BEAUTY SALTA",
    69510727: "CAPELLI JUJUY - IDRAET TUCUMAN",
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def formato_pesos(valor):
    """Formatea un número como $ 1.234.567,89"""
    if pd.isna(valor):
        return ""
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formato_pesos_corto(valor):
    """Formatea un número para gráficos: $ 1,2M"""
    if pd.isna(valor):
        return ""
    if abs(valor) >= 1_000_000:
        return f"$ {valor/1_000_000:,.1f}M".replace(".", ",")
    if abs(valor) >= 1_000:
        return f"$ {valor/1_000:,.0f}K".replace(".", ",")
    return f"$ {valor:,.0f}"


def nombre_terminal(numero):
    """Devuelve el nombre de la sucursal para un número de terminal."""
    try:
        numero = int(numero)
    except (ValueError, TypeError):
        return f"Terminal {numero}"
    return TERMINALES.get(numero, f"Terminal {numero} (sin nombre)")


# ============================================================
# TÍTULO
# ============================================================
st.title("💳 Resumen de Transacciones")

# ============================================================
# CARGA DEL ARCHIVO
# ============================================================
archivo = st.file_uploader("📁 Subí el archivo Excel", type=["xlsx"])

if archivo is None:
    st.info("👆 Subí un archivo Excel para comenzar.")
    st.stop()

df = pd.read_excel(archivo, sheet_name="Transacciones")
df.columns = df.columns.str.strip()
df["Monto total"] = pd.to_numeric(df["Monto total"], errors="coerce").fillna(0)

# Separar compras y anulaciones
compras = df[df["Tipo de transacción"].str.lower() == "compra"].copy()
anulaciones = df[df["Tipo de transacción"].str.lower() == "anulación"].copy()

# Convertir tipos
compras["Cuotas"] = pd.to_numeric(compras["Cuotas"], errors="coerce").fillna(0).astype(int)
compras["Terminal"] = pd.to_numeric(compras["Terminal"], errors="coerce").fillna(0).astype(int)
compras["Sucursal"] = compras["Terminal"].apply(nombre_terminal)

# ============================================================
# SIDEBAR - FILTROS
# ============================================================
st.sidebar.header("🔍 Filtros")

# Filtro por sucursal
sucursales_disponibles = sorted(compras["Sucursal"].unique().tolist())
sucursales_sel = st.sidebar.multiselect(
    "Sucursales",
    options=sucursales_disponibles,
    default=sucursales_disponibles,
)

# Filtro por marca (producto)
marcas_disponibles = sorted(compras["Producto"].dropna().unique().tolist())
marcas_sel = st.sidebar.multiselect(
    "Marcas de tarjeta",
    options=marcas_disponibles,
    default=marcas_disponibles,
)

# Filtro por cuotas
cuotas_disponibles = sorted(compras["Cuotas"].unique().tolist())
cuotas_sel = st.sidebar.multiselect(
    "Cuotas",
    options=cuotas_disponibles,
    default=cuotas_disponibles,
)

# Aplicar filtros
compras_f = compras[
    (compras["Sucursal"].isin(sucursales_sel))
    & (compras["Producto"].isin(marcas_sel))
    & (compras["Cuotas"].isin(cuotas_sel))
].copy()

# ============================================================
# VERIFICAR QUE HAYA DATOS
# ============================================================
if compras_f.empty:
    st.warning("⚠️ No hay datos con los filtros seleccionados. Probá cambiar los filtros.")
    st.stop()

# ============================================================
# KPIs PRINCIPALES
# ============================================================
total = compras_f["Monto total"].sum()
cantidad = len(compras_f)
ticket_promedio = total / cantidad if cantidad > 0 else 0
cant_anulaciones = len(anulaciones)
monto_anulaciones = anulaciones["Monto total"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Importe total", formato_pesos(total))
col2.metric("🧾 Transacciones", f"{cantidad:,}".replace(",", "."))
col3.metric("🎯 Ticket promedio", formato_pesos(ticket_promedio))
col4.metric(
    "⚠️ Anulaciones",
    f"{cant_anulaciones}",
    delta=f"-{formato_pesos(monto_anulaciones)}" if cant_anulaciones > 0 else None,
    delta_color="inverse",
)

st.divider()

# ============================================================
# PESTAÑAS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Resumen general",
    "📇 Marcas y cuotas",
    "🏪 Sucursales",
    "📈 Análisis",
    "📥 Datos y exportar",
])

# ------------------------------------------------------------
# TAB 1: RESUMEN GENERAL
# ------------------------------------------------------------
with tab1:
    st.subheader("Vista general")

    col_a, col_b = st.columns(2)

    # Gráfico: Top marcas
    with col_a:
        st.markdown("##### Top marcas de tarjeta")
        top_marcas = (
            compras_f.groupby("Producto")["Monto total"]
            .sum()
            .sort_values(ascending=True)
            .reset_index()
        )
        fig = px.bar(
            top_marcas,
            x="Monto total",
            y="Producto",
            orientation="h",
            color="Monto total",
            color_continuous_scale="Blues",
            text="Monto total",
        )
        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            textfont_size=11,
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico: Top sucursales
    with col_b:
        st.markdown("##### Top sucursales")
        top_suc = (
            compras_f.groupby("Sucursal")["Monto total"]
            .sum()
            .sort_values(ascending=True)
            .reset_index()
        )
        fig = px.bar(
            top_suc,
            x="Monto total",
            y="Sucursal",
            orientation="h",
            color="Monto total",
            color_continuous_scale="Greens",
            text="Monto total",
        )
        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            textfont_size=11,
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 2: MARCAS Y CUOTAS
# ------------------------------------------------------------
with tab2:
    st.subheader("📇 Marcas de tarjeta y cuotas")

    tabla_cuotas = pd.pivot_table(
        compras_f,
        values="Monto total",
        index="Producto",
        columns="Cuotas",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Total",
    )
    tabla_cuotas.index.name = "Producto"

    st.dataframe(
        tabla_cuotas.style.format(formato_pesos),
        use_container_width=True,
        height=350,
    )

    st.divider()

    # Gráfico de barras apiladas: marcas × cuotas
    st.markdown("##### Distribución de cuotas por marca")
    pivot_sin_total = pd.pivot_table(
        compras_f,
        values="Monto total",
        index="Producto",
        columns="Cuotas",
        aggfunc="sum",
        fill_value=0,
    )
    fig = px.bar(
        pivot_sin_total,
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        height=450,
        xaxis_title="Marca",
        yaxis_title="Monto",
        legend_title="Cuotas",
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 3: SUCURSALES
# ------------------------------------------------------------
with tab3:
    st.subheader("🏪 Análisis por sucursal")

    col_a, col_b = st.columns([1, 1])

    por_suc = (
        compras_f.groupby("Sucursal")["Monto total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    # Tabla
    with col_a:
        st.markdown("##### Detalle")
        tabla_suc = por_suc.copy()
        tabla_suc["% del total"] = (tabla_suc["Monto total"] / total * 100).round(2)
        st.dataframe(
            tabla_suc.style.format({
                "Monto total": formato_pesos,
                "% del total": "{:.2f}%",
            }),
            use_container_width=True,
            height=400,
            hide_index=True,
        )

    # Torta
    with col_b:
        st.markdown("##### Participación")
        fig = px.pie(
            por_suc,
            names="Sucursal",
            values="Monto total",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            textfont_size=11,
        )
        fig.update_layout(
            height=400,
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: ANÁLISIS
# ------------------------------------------------------------
with tab4:
    st.subheader("📈 Análisis avanzado")

    col_a, col_b = st.columns(2)

    # Por cuotas
    with col_a:
        st.markdown("##### Monto por cantidad de cuotas")
        por_cuotas = (
            compras_f.groupby("Cuotas")["Monto total"]
            .sum()
            .reset_index()
            .sort_values("Cuotas")
        )
        fig = px.bar(
            por_cuotas,
            x="Cuotas",
            y="Monto total",
            text="Monto total",
            color="Monto total",
            color_continuous_scale="Purples",
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(
            height=380,
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Cuotas",
            yaxis_title="Monto",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Por adquirente
    with col_b:
        st.markdown("##### Monto por adquirente")
        por_adq = (
            compras_f.groupby("Adquirente")["Monto total"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig = px.bar(
            por_adq,
            x="Adquirente",
            y="Monto total",
            text="Monto total",
            color="Adquirente",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(
            height=380,
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="",
            yaxis_title="Monto",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Heatmap: Marca x Cuotas
    st.markdown("##### Mapa de calor: Marca × Cuotas")
    pivot_heat = pd.pivot_table(
        compras_f,
        values="Monto total",
        index="Producto",
        columns="Cuotas",
        aggfunc="sum",
        fill_value=0,
    )
    fig = px.imshow(
        pivot_heat,
        text_auto=".2s",
        aspect="auto",
        color_continuous_scale="YlGnBu",
    )
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="Cuotas",
        yaxis_title="Marca",
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 5: DATOS Y EXPORTAR
# ------------------------------------------------------------
with tab5:
    st.subheader("📥 Datos filtrados y exportación")

    st.markdown(f"**{len(compras_f)} transacciones** con los filtros actuales.")

    st.dataframe(
        compras_f[[
            "Fecha", "Terminal", "Sucursal", "Producto",
            "Cuotas", "Adquirente", "Monto total"
        ]].style.format({"Monto total": formato_pesos}),
        use_container_width=True,
        height=400,
        hide_index=True,
    )

    st.divider()

    # --- EXPORTAR A EXCEL ---
    st.markdown("##### 📤 Descargar resumen en Excel")

    from io import BytesIO

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Hoja 1: resumen marcas y cuotas
        pivot_export = pd.pivot_table(
            compras_f,
            values="Monto total",
            index="Producto",
            columns="Cuotas",
            aggfunc="sum",
            fill_value=0,
            margins=True,
            margins_name="Total",
        )
        pivot_export.to_excel(writer, sheet_name="Marcas y cuotas")

        # Hoja 2: por sucursal
        por_suc_export = (
            compras_f.groupby("Sucursal")["Monto total"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        por_suc_export.to_excel(writer, sheet_name="Sucursales", index=False)

        # Hoja 3: datos crudos
        compras_f.to_excel(writer, sheet_name="Datos", index=False)

    st.download_button(
        label="⬇️ Descargar resumen (.xlsx)",
        data=buffer.getvalue(),
        file_name="resumen_transacciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ------------------------------------------------------------
# Pie
# ------------------------------------------------------------
st.divider()
st.caption("💡 Tip: usá los filtros del panel izquierdo para acotar los datos. Todas las vistas se actualizan solas.")