import streamlit as st
import pandas as pd

st.set_page_config(page_title="Resumen de Transacciones", layout="wide")
st.title("📊 Resumen de Transacciones")

# --- Cargar archivo ---
archivo = st.file_uploader("Subí el Excel", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo, sheet_name="Transacciones")

    # Limpieza básica
    df.columns = df.columns.str.strip()
    df["Monto total"] = pd.to_numeric(df["Monto total"], errors="coerce").fillna(0)

    # Separar compras y anulaciones
    compras = df[df["Tipo de transacción"].str.lower() == "compra"]
    anulaciones = df[df["Tipo de transacción"].str.lower() == "anulación"]

    # --- BOTÓN ---
    if st.button("Calcular resumen"):
        total = compras["Monto total"].sum()
        st.metric("💰 Importe total (compras)", f"$ {total:,.2f}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Por marca de tarjeta")
            por_marca = (
                compras.groupby("Producto")["Monto total"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )
            st.dataframe(por_marca, use_container_width=True)

        with col2:
            st.subheader("Por número de terminal")
            por_terminal = (
                compras.groupby("Terminal")["Monto total"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )
            st.dataframe(por_terminal, use_container_width=True)

        if not anulaciones.empty:
            st.warning(f"⚠️ Hay {len(anulaciones)} anulaciones por $ {anulaciones['Monto total'].sum():,.2f}")