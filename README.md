# 🧠 LL(1) Grammar Analyzer & Parser Toolkit

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://analyzer-ll1.streamlit.app/)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Una suite completa para el análisis y transformación de gramáticas LL(1) con capacidades interactivas de parsing.


## 🌟 Características Principales

### 🔍 Análisis Gramatical Avanzado
- Transformación de gramáticas a formato LL(1)
- Cálculo automático de conjuntos First y Follow
- Generación de tablas de parsing LL(1)
- Visualización interactiva de resultados

### 🛠️ Herramientas de Transformación
- Eliminación de recursión izquierda
- Factorización de prefijos comunes
- Normalización de gramáticas
- Validación de propiedades LL(1)

### 📊 Parsing Interactivo
- Analizador paso a paso
- Visualización de la pila de parsing
- Diagnóstico de errores detallado
- Soporte para múltiples estrategias de recuperación

## 🚀 Demo en Vivo

Prueba la aplicación directamente en tu navegador:  
👉 [https://analyzer-ll1.streamlit.app/](https://analyzer-ll1.streamlit.app/)

## 📦 Instalación Local

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación
```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/ll1-analyzer.git

# Navegar al directorio del proyecto
cd ll1-analyzer

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
