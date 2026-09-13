import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(page_title="Control Financiero Personal", page_icon="💰", layout="wide")

# Nombre del archivo para guardar los datos locales (como alternativa si no usas Firebase/Google Sheets en esta prueba)
DATA_FILE = "movimientos_personales.csv"

# Categorías predefinidas (basadas en la estructura de tu archivo y finanzas personales)
CATEGORIAS_INGRESO = ["Sueldo", "Servicios Profesionales", "Rendimientos Financieros", "Ventas", "Otros Ingresos"]
CATEGORIAS_GASTO = ["Alimentación", "Vivienda / Servicios", "Transporte", "Tarjetas de Crédito / Cuotas", "Ocio / Entretenimiento", "Salud", "Educación", "Otros Gastos"]

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    else:
        return pd.DataFrame(columns=["Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Forma de Pago"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def main():
    st.title("💰 Mi Control Financiero Personal")
    
    df = load_data()

    # --- BARRA LATERAL: NUEVO REGISTRO ---
    st.sidebar.header("➕ Nuevo Movimiento")
    with st.sidebar.form("nuevo_movimiento"):
        fecha = st.date_input("Fecha", datetime.today())
        tipo = st.selectbox("Tipo de Movimiento", ["Gasto", "Ingreso"])
        
        # Las categorías cambian según el tipo
        if tipo == "Ingreso":
            categoria = st.selectbox("Categoría", CATEGORIAS_INGRESO)
        else:
            categoria = st.selectbox("Categoría", CATEGORIAS_GASTO)
            
        descripcion = st.text_input("Descripción (Ej: Compra súper, Pago luz)")
        monto = st.number_input("Monto ($)", min_value=0.01, step=100.0)
        forma_pago = st.selectbox("Medio de Pago", ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia / Mercado Pago"])
        
        submit = st.form_submit_button("Guardar Registro")
        
        if submit:
            nuevo_registro = pd.DataFrame([{
                "Fecha": fecha,
                "Tipo": tipo,
                "Categoría": categoria,
                "Descripción": descripcion,
                "Monto": monto,
                "Forma de Pago": forma_pago
            }])
            df = pd.concat([df, nuevo_registro], ignore_index=True)
            save_data(df)
            st.sidebar.success("✅ Registro guardado!")
            st.rerun() # Recarga la app para mostrar el nuevo dato

    # --- PANTALLA PRINCIPAL ---
    if df.empty:
        st.info("👋 ¡Bienvenido! Usa el panel izquierdo para registrar tu primer ingreso o gasto.")
    else:
        # Filtros de mes
        st.subheader("📅 Resumen del Mes")
        df['Mes'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m')
        meses_disponibles = sorted(df['Mes'].unique(), reverse=True)
        mes_seleccionado = st.selectbox("Selecciona el mes a analizar:", meses_disponibles)
        
        df_mes = df[df['Mes'] == mes_seleccionado]
        
        # Cálculos de totales
        ingresos_mes = df_mes[df_mes['Tipo'] == 'Ingreso']['Monto'].sum()
        gastos_mes = df_mes[df_mes['Tipo'] == 'Gasto']['Monto'].sum()
        saldo_mes = ingresos_mes - gastos_mes
        
        # Mostrar KPIs
        col1, col2, col3 = st.columns(3)
        col1.metric("Ingresos", f"${ingresos_mes:,.2f}")
        col2.metric("Gastos", f"${gastos_mes:,.2f}")
        col3.metric("Saldo Mensual", f"${saldo_mes:,.2f}", delta=saldo_mes)

        st.write("---")
        
        # Gráficos
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 💸 Distribución de Gastos")
            df_gastos = df_mes[df_mes['Tipo'] == 'Gasto']
            if not df_gastos.empty:
                fig_gastos = px.pie(df_gastos, names='Categoría', values='Monto', hole=0.4)
                st.plotly_chart(fig_gastos, use_container_width=True)
            else:
                st.write("No hay gastos registrados este mes.")

        with c2:
            st.markdown("#### 📈 Ingresos vs Gastos")
            if not df_mes.empty:
                resumen_tipo = df_mes.groupby('Tipo')['Monto'].sum().reset_index()
                fig_barras = px.bar(resumen_tipo, x='Tipo', y='Monto', color='Tipo', 
                                    color_discrete_map={'Ingreso': 'green', 'Gasto': 'red'})
                st.plotly_chart(fig_barras, use_container_width=True)

        st.write("---")
        st.markdown("#### 📋 Historial de Movimientos")
        
        # Mostrar la tabla formateada
        df_mostrar = df_mes.drop(columns=['Mes']).sort_values('Fecha', ascending=False)
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        
        # Botón para borrar datos (opcional)
        with st.expander("⚙️ Opciones avanzadas"):
            if st.button("Borrar historial del mes seleccionado"):
                df_restante = df[df['Mes'] != mes_seleccionado].drop(columns=['Mes'], errors='ignore')
                save_data(df_restante)
                st.success("Mes borrado. Recargando...")
                st.rerun()

if __name__ == "__main__":
    main()
