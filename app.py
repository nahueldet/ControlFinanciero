import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Control Financiero Personal", page_icon="💰", layout="wide")

DATA_FILE = "movimientos_personales.csv"

CATEGORIAS_INGRESO = ["Sueldo", "Servicios Profesionales", "Rendimientos Financieros", "Ventas", "Otros Ingresos"]
CATEGORIAS_GASTO = ["Alimentación", "Vivienda / Servicios", "Transporte", "Tarjetas / Cuotas", "Ocio / Entretenimiento", "Salud", "Educación", "Otros Gastos"]
TARJETAS_DISPONIBLES = ["Ninguna", "Visa", "Mastercard", "American Express", "Naranja", "Otra"]

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Asegurar que todas las columnas existan en archivos viejos
        if 'ID' not in df.columns:
            df['ID'] = [str(uuid.uuid4()) for _ in range(len(df))]
        if 'Tarjeta' not in df.columns:
            df['Tarjeta'] = "Ninguna"
        return df
    else:
        return pd.DataFrame(columns=["ID", "Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Forma de Pago", "Tarjeta"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def main():
    st.title("💰 Mi Control Financiero Personal")
    
    df = load_data()

    # --- BARRA LATERAL: NUEVO REGISTRO ---
    st.sidebar.header("➕ Nuevo Movimiento")
    with st.sidebar.form("nuevo_movimiento", clear_on_submit=True):
        fecha = st.date_input("Fecha", datetime.today())
        tipo = st.selectbox("Tipo de Movimiento", ["Gasto", "Ingreso"])
        
        categoria = st.selectbox("Categoría", CATEGORIAS_INGRESO if tipo == "Ingreso" else CATEGORIAS_GASTO)
            
        descripcion = st.text_input("Descripción (Ej: Compra súper, Venta mostrador)")
        monto = st.number_input("Monto ($)", min_value=0.01, step=100.0)
        
        forma_pago = st.selectbox("Medio de Pago", ["Efectivo", "Tarjeta de Crédito", "Tarjeta de Débito", "Transferencia / Billetera Virtual"])
        
        # Selección de tarjeta solo si aplica
        if forma_pago in ["Tarjeta de Crédito", "Tarjeta de Débito"]:
            tarjeta = st.selectbox("¿Qué Tarjeta usaste?", [t for t in TARJETAS_DISPONIBLES if t != "Ninguna"])
        else:
            tarjeta = "Ninguna"
            # Ocultamos el selector usando un elemento inactivo, pero mantenemos la variable
            st.selectbox("¿Qué Tarjeta usaste?", ["No aplica"], disabled=True) 
        
        submit = st.form_submit_button("Guardar Registro")
        
        if submit:
            nuevo_registro = pd.DataFrame([{
                "ID": str(uuid.uuid4()),
                "Fecha": fecha.strftime("%Y-%m-%d"),
                "Tipo": tipo,
                "Categoría": categoria,
                "Descripción": descripcion,
                "Monto": monto,
                "Forma de Pago": forma_pago,
                "Tarjeta": tarjeta
            }])
            df = pd.concat([df, nuevo_registro], ignore_index=True)
            save_data(df)
            st.sidebar.success("✅ Registro guardado!")
            st.rerun()

    # --- PANTALLA PRINCIPAL ---
    if df.empty:
        st.info("👋 ¡Bienvenido! Usa el panel izquierdo para registrar tu primer ingreso o gasto.")
    else:
        # Pestañas de navegación principal
        tab_resumen, tab_tarjetas, tab_editar = st.tabs(["📊 Resumen General", "💳 Consumos por Tarjeta", "✏️ Editar Registros"])
        
        df['Mes'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m')
        meses_disponibles = sorted(df['Mes'].unique(), reverse=True)
        
        with tab_resumen:
            mes_seleccionado = st.selectbox("📅 Selecciona el mes a analizar:", meses_disponibles, key="select_mes_resumen")
            df_mes = df[df['Mes'] == mes_seleccionado]
            
            ingresos_mes = df_mes[df_mes['Tipo'] == 'Ingreso']['Monto'].sum()
            gastos_mes = df_mes[df_mes['Tipo'] == 'Gasto']['Monto'].sum()
            saldo_mes = ingresos_mes - gastos_mes
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Ingresos", f"${ingresos_mes:,.2f}")
            col2.metric("Gastos", f"${gastos_mes:,.2f}")
            col3.metric("Saldo Mensual", f"${saldo_mes:,.2f}", delta=saldo_mes)

            st.write("---")
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
                st.markdown("#### 📋 Historial del Mes")
                df_mostrar = df_mes.drop(columns=['Mes', 'ID']).sort_values('Fecha', ascending=False)
                st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        with tab_tarjetas:
            st.markdown("### 💳 Análisis de Consumos con Tarjetas")
            st.write("Aquí puedes ver cuánto has gastado en total agrupado por cada tarjeta utilizada.")
            
            mes_tarjetas = st.selectbox("📅 Selecciona el mes:", meses_disponibles, key="select_mes_tarjetas")
            df_mes_tarjetas = df[(df['Mes'] == mes_tarjetas) & (df['Tipo'] == 'Gasto') & (df['Tarjeta'] != 'Ninguna')]
            
            if not df_mes_tarjetas.empty:
                resumen_tarjetas = df_mes_tarjetas.groupby('Tarjeta')['Monto'].sum().reset_index()
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.dataframe(resumen_tarjetas.style.format({'Monto': '${:,.2f}'}), use_container_width=True, hide_index=True)
                with c2:
                    fig_tarjetas = px.bar(resumen_tarjetas, x='Tarjeta', y='Monto', color='Tarjeta', title="Total de Gastos por Tarjeta")
                    st.plotly_chart(fig_tarjetas, use_container_width=True)
                    
                st.markdown("#### Detalle de consumos:")
                st.dataframe(df_mes_tarjetas[['Fecha', 'Tarjeta', 'Categoría', 'Descripción', 'Monto']].sort_values('Fecha'), use_container_width=True, hide_index=True)
            else:
                st.info("No hay gastos registrados con tarjeta para el mes seleccionado.")

        with tab_editar:
            st.markdown("### ✏️ Corregir o Eliminar Registros")
            st.write("Selecciona un registro de la lista para modificar su monto o eliminarlo por completo si te equivocaste.")
            
            # Selector de registro a editar
            df_display = df.copy()
            df_display['Filtro'] = df_display['Fecha'] + " | " + df_display['Tipo'] + " | " + df_display['Descripción'] + " | $" + df_display['Monto'].astype(str)
            
            registro_seleccionado = st.selectbox("Selecciona el registro a editar:", df_display['Filtro'].tolist())
            
            if registro_seleccionado:
                # Obtener el ID del registro seleccionado
                id_seleccionado = df_display[df_display['Filtro'] == registro_seleccionado]['ID'].values[0]
                fila_editar = df[df['ID'] == id_seleccionado].iloc[0]
                
                with st.form("form_edicion"):
                    st.write(f"Editando: **{fila_editar['Descripción']}**")
                    nuevo_monto = st.number_input("Corregir Monto ($)", value=float(fila_editar['Monto']), step=100.0)
                    nueva_desc = st.text_input("Corregir Descripción", value=fila_editar['Descripción'])
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        btn_guardar = st.form_submit_button("Actualizar Registro", type="primary")
                    with c2:
                        btn_eliminar = st.form_submit_button("Eliminar Registro")
                        
                    if btn_guardar:
                        df.loc[df['ID'] == id_seleccionado, 'Monto'] = nuevo_monto
                        df.loc[df['ID'] == id_seleccionado, 'Descripción'] = nueva_desc
                        save_data(df)
                        st.success("Registro actualizado. Recargando...")
                        st.rerun()
                        
                    if btn_eliminar:
                        df = df[df['ID'] != id_seleccionado]
                        save_data(df)
                        st.warning("Registro eliminado. Recargando...")
                        st.rerun()

if __name__ == "__main__":
    main()
