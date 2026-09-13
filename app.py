import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuración inicial de la página
st.set_page_config(page_title="Dashboard Financiero", page_icon="📊", layout="wide")

def main():
    st.title("📊 Panel de Control Financiero")
    
    # 1. Carga del archivo Excel
    archivo_excel = "Control Financiero Completo.xlsx"
    
    if not os.path.exists(archivo_excel):
        st.error(f"No se encontró el archivo: {archivo_excel}. Asegúrate de que esté en la misma carpeta que este script.")
        st.stop()
        
    @st.cache_data
    def cargar_datos(ruta):
        xls = pd.ExcelFile(ruta)
        # Leer todas las hojas en un diccionario de DataFrames
        return {hoja: pd.read_excel(xls, sheet_name=hoja) for hoja in xls.sheet_names}

    try:
        datos = cargar_datos(archivo_excel)
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        st.stop()

    # 2. Barra lateral para navegación
    st.sidebar.header("⚙️ Configuración del Panel")
    nombres_hojas = list(datos.keys())
    hoja_actual = st.sidebar.selectbox("Selecciona la hoja a visualizar:", nombres_hojas)
    
    df = datos[hoja_actual]
    
    st.subheader(f"Datos base: {hoja_actual}")
    st.dataframe(df, use_container_width=True)

    st.write("---")
    
    # 3. Asignación dinámica de columnas
    st.sidebar.subheader("Mapeo de Variables")
    st.sidebar.write("Asigna las columnas para generar tu reporte visual.")
    
    columnas = df.columns.tolist()
    
    # Función para intentar autodetectar columnas comunes
    def buscar_col(palabras_clave):
        for col in columnas:
            if any(palabra in str(col).lower() for palabra in palabras_clave):
                return columnas.index(col)
        return 0

    idx_fecha = buscar_col(['fecha', 'date', 'mes', 'registro'])
    idx_monto = buscar_col(['monto', 'valor', 'total', 'precio', 'saldo', 'costo'])
    idx_cat = buscar_col(['ingreso', 'gasto', 'tipo', 'categor', 'concepto', 'cuenta'])

    # Selectores para el usuario
    col_fecha = st.sidebar.selectbox("Columna de Fecha (Opcional)", ["Ninguna"] + columnas, index=idx_fecha + 1 if idx_fecha else 0)
    col_monto = st.sidebar.selectbox("Columna de Monto/Valor", ["Ninguna"] + columnas, index=idx_monto + 1 if idx_monto else 0)
    col_categoria = st.sidebar.selectbox("Columna de Categoría", ["Ninguna"] + columnas, index=idx_cat + 1 if idx_cat else 0)

    # 4. Generación de Gráficos si las columnas están configuradas
    if col_monto != "Ninguna" and col_categoria != "Ninguna":
        st.subheader("📈 Resumen de Indicadores")
        
        # Limpieza de datos para cálculos
        df_clean = df.dropna(subset=[col_monto, col_categoria]).copy()
        df_clean[col_monto] = pd.to_numeric(df_clean[col_monto], errors='coerce').fillna(0)
        
        # Agrupar datos por la categoría seleccionada
        resumen = df_clean.groupby(col_categoria)[col_monto].sum().reset_index()
        
        # Mostrar métrica principal
        col1, col2 = st.columns([1, 3])
        total = df_clean[col_monto].sum()
        col1.metric("Monto Total Registrado", f"${total:,.2f}")
        
        # Visualizaciones
        st.write("---")
        c1, c2 = st.columns(2)
        
        with c1:
            fig_bar = px.bar(resumen, x=col_categoria, y=col_monto, title="Distribución por Categoría (Barras)", color=col_categoria)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            fig_pie = px.pie(resumen, names=col_categoria, values=col_monto, title="Proporción de Montos (Circular)")
            st.plotly_chart(fig_pie, use_container_width=True)
            
    else:
        st.info("💡 Por favor, configura las columnas de 'Monto' y 'Categoría' en la barra lateral para desplegar los gráficos interactivos.")

if __name__ == "__main__":
    main()
