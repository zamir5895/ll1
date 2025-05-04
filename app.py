
from tokenize import group
import streamlit as st
from collections import defaultdict
import streamlit.components.v1 as components

import streamlit as st
from streamlit_extras.colored_header import colored_header
from streamlit_extras.card import card
from streamlit_extras.stylable_container import stylable_container
import time
import pandas as pd


# Configuración de la página
st.set_page_config(
    page_title="LL(1) Analyzer Pro",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)
EPSILON='ε'

DEFAULT_GRAMMAR="""
E -> E + T | T
T -> T * F | F
F -> ( E ) | id
"""

def inicializacion():
  defaults = {
      'grammar_input':DEFAULT_GRAMMAR,
      'is_ll1':True,
      'transformed_grammar':None,
      'pasos':[],
      'cadena_input':'',
      'first':[],
      'follow':[],
      'tabla_simbolos':[],
      'cadena':"",
      'cadena_procesada': [],

  }
  for k, v in defaults.items():
    if k not in st.session_state:
      st.session_state[k] = v

def procesamiento_gramatica(rules):
  nonterms=[]
  for r in rules:
    if '->' not in r:continue
    lhs = r.split('->', 1)[0].strip()
    if lhs not in nonterms:
      nonterms.append(lhs)
  return nonterms

def tiene_recursion_por_izquierda(rules,nonterms):
  for r in rules:
    if '->' not in r:continue
    i,d = map(str.strip, r.split('->',1))
    for prod in map(str.strip, d.split('!')):
      p_s = prod.split()[0] if prod else ''
      if p_s == i:
        return True
  p_simbolos = defaultdict(list)
  for nt in nonterms:
    p_simbolos[nt] = []
  for r in rules:
    if '->' not in r:
      continue
    i, d = map(str.strip, r.split('->', 1))
    for prod in map(str.strip, d.split('|')):
      if not prod:
        continue
      first = prod.split()[0]
      if first in nonterms:
        p_simbolos[i].append(first)
    visitados = set()

    def encontrar_ciclos(simbolo, p):
      if simbolo in visitados:
        return True
      p.add(simbolo)
      for s in p_simbolos[simbolo]:
        if encontrar_ciclos(s, p.copy()):
          return True
      return False

    for nt in nonterms:
      if encontrar_ciclos(nt, set()):
        return True
  return False




def tiene_factorizacion_por_izquierda(rules,nonterms):
  prods = defaultdict(list)
  for r in rules:
    if '->' not in r:
      continue
    i, d = map(str.strip, r.split('->', 1))
    for a in d.split('|'):
      prods[i].append(a.strip().split())

  for n in nonterms:
    producciones = prods.get(n, [])
    prefijos = set()
    for prod in producciones:
      if prod:
        prefijo = prod[0]
        if prefijo in prefijos:
          return True
        prefijos.add(prefijo)
  return False



def eliminacion_recursion_por_izquierda(rules, nonterms):
    nuevas_reglas = []
    pasos = []
    prods = defaultdict(list)

    for r in rules:
        if '->' not in r: continue
        i, d = map(str.strip, r.split('->', 1))
        prods[i] = [alt.strip().split() for alt in d.split('|') if alt.strip()]

    for n in sorted(nonterms):
        alfas = []
        betas = []

        for prod in prods.get(n, []):
            if prod and prod[0] == n:
                alfas.append(prod[1:])
            else:
                betas.append(prod)

        if alfas:
            n_prime = n + "'"
            pasos.append(f"Transformando {n} para eliminar recursión izquierda")

            for beta in betas:
                nuevas_reglas.append(f"{n} -> {' '.join(beta) if beta else ''} {n_prime}".strip())

            for alfa in alfas:
                nuevas_reglas.append(f"{n_prime} -> {' '.join(alfa)} {n_prime}".strip())

            nuevas_reglas.append(f"{n_prime} -> {EPSILON}")
        else:
            for beta in betas:
                nuevas_reglas.append(f"{n} -> {' '.join(beta)}".strip())

    return nuevas_reglas, pasos

def eliminar_factorizacion_por_izquierda(rules, nonterms):
    nuevas_reglas = []
    pasos = []
    prods = defaultdict(list)

    for regla in rules:
        if '->' not in regla:
            continue
        izquierda, derecha = map(str.strip, regla.split('->', 1))
        alternativas = [alt.strip().split() for alt in derecha.split('|')]
        prods[izquierda].extend(alternativas)

    for nt in nonterms:
        producciones = prods[nt]
        prefijos = defaultdict(list)

        for prod in producciones:
            if prod:
                prefijos[prod[0]].append(prod)

        hubo_factorizacion = False
        for prefijo, grupo in prefijos.items():
            if len(grupo) > 1:
                hubo_factorizacion = True
                nuevo_nt = f"{nt}'"
                pasos.append(f"Se factoriza por izquierda en {nt} con prefijo común '{prefijo}'")

                nuevas_reglas.append(f"{nt} -> {prefijo} {nuevo_nt}")

                for prod in grupo:
                    sufijo = prod[1:]
                    if sufijo:
                        nuevas_reglas.append(f"{nuevo_nt} -> {' '.join(sufijo)}")
                    else:
                        nuevas_reglas.append(f"{nuevo_nt} -> {EPSILON}")
            else:
                nuevas_reglas.append(f"{nt} -> {' '.join(grupo[0])}")

        if not hubo_factorizacion:
            for prod in producciones:
                nuevas_reglas.append(f"{nt} -> {' '.join(prod)}")

    return nuevas_reglas, pasos


def is_ll1(rules, nonterms):
  if tiene_recursion_por_izquierda(rules,nonterms):
    return False
  if tiene_factorizacion_por_izquierda(rules,nonterms):
    return False
  return True


def transformar_a_ll1(rules, nonterms, r, f):
    if r and not f:
        return eliminacion_recursion_por_izquierda(rules, nonterms)
    elif not r and f:
        return eliminar_factorizacion_por_izquierda(rules, nonterms)
    elif r and f:
        reglas_sin_recursion, pasos1 = eliminacion_recursion_por_izquierda(rules, nonterms)
        reglas_sin_factorizacion, pasos2 = eliminar_factorizacion_por_izquierda(reglas_sin_recursion, nonterms)
        return reglas_sin_factorizacion, pasos1 + pasos2
    else:
        return rules, ["No se aplicó ninguna transformación."]


def trim_elements(elements):
  return[e.strip() for e in elements if e.strip()]


def add_unique(element, array):
  if element not in array:
    array.append(element)
    return True
  return False


def proccess_ll1(reglas):
  alfabeto = []
  nonterminals = []
  terminals = []
  for r in reglas:
    partes = r.split('->')
    if len(partes) != 2:
      continue

    nonterminal = partes[0].strip()
    d = trim_elements(partes[1].strip().split())
    add_unique(nonterminal,alfabeto)
    add_unique(nonterminal,nonterminals)

    for s in d:
      if s != EPSILON:
        add_unique(s,alfabeto)

  for s in alfabeto:
    if s not in nonterminals:
      add_unique(s,terminals)
  return alfabeto, nonterminals, terminals


def obtener_firsts(reglas, nonterminals, terminals):
    firsts = {}
    cambio = True

    for nt in nonterminals:
        firsts[nt] = []

    while cambio:
        cambio = False
        for regla in reglas:
            partes = regla.split('->')
            if len(partes) != 2:
                continue

            nonterminal = partes[0].strip()
            desarrollo = trim_elements(partes[1].strip().split())

            # Caso 1: Producción es ε
            if len(desarrollo) == 1 and desarrollo[0] == EPSILON:
                if add_unique(EPSILON, firsts[nonterminal]):
                    cambio = True

            # Caso 2: Producción no es ε
            else:
                deriva_epsilon = True
                for simbolo in desarrollo:
                    if simbolo in terminals:
                        if add_unique(simbolo, firsts[nonterminal]):
                            cambio = True
                        deriva_epsilon = False
                        break

                    elif simbolo in nonterminals:
                        # Agregar FIRST(simbolo) - {ε} a FIRST(nonterminal)
                        for first_simbolo in firsts[simbolo]:
                            if first_simbolo != EPSILON and add_unique(first_simbolo, firsts[nonterminal]):
                                cambio = True

                        if EPSILON not in firsts[simbolo]:
                            deriva_epsilon = False
                            break

                # Si todos pueden derivar ε, agregar ε
                if deriva_epsilon and add_unique(EPSILON, firsts[nonterminal]):
                    cambio = True

    return firsts


def obtener_first_en_secuencia(secuencia, firsts, terminals, nonterminals):
    result = []
    deriva_epsilon = True  # Asumimos inicialmente que toda la secuencia puede derivar ε

    for simbolo in secuencia:
        if simbolo in terminals:
            # Regla 1: Si es terminal, agregarlo y terminar
            add_unique(simbolo, result)
            deriva_epsilon = False
            break

        elif simbolo in nonterminals:
            # Regla 2: Si es no terminal, agregar su FIRST (excepto ε)
            for first_sim in firsts.get(simbolo, []):
                if first_sim != EPSILON:
                    add_unique(first_sim, result)

            # Si el no terminal no puede derivar ε, terminar
            if EPSILON not in firsts.get(simbolo, []):
                deriva_epsilon = False
                break

    # Regla 3: Si todos pueden derivar ε, agregar ε
    if deriva_epsilon:
        add_unique(EPSILON, result)

    return result

def obtener_los_follows(reglas, nonterminals, firsts, terminals):
    follows = {}
    for nt in nonterminals:
        follows[nt] = []

    # Paso 1: $ está en FOLLOW(S) donde S es el símbolo inicial
    if nonterminals:
        follows[nonterminals[0]].append('$')

    cambio = True

    while cambio:
        cambio = False
        for regla in reglas:
            partes = regla.split('->')
            if len(partes) != 2:
                continue

            A = partes[0].strip()  # Lado izquierdo de la producción (A -> α)
            α = trim_elements(partes[1].strip().split())

            for i, B in enumerate(α):
                if B in nonterminals:
                    # Regla 1: A -> αBβ, añadir FIRST(β)-{ε} a FOLLOW(B)
                    if i < len(α) - 1:
                        β = α[i+1:]
                        first_β = obtener_first_en_secuencia(β, firsts, terminals, nonterminals)

                        for simbolo in first_β:
                            if simbolo != EPSILON and add_unique(simbolo, follows[B]):
                                cambio = True

                    # Regla 2: A -> αB o A -> αBβ donde β =>* ε
                    if i == len(α) - 1 or EPSILON in obtener_first_en_secuencia(α[i+1:], firsts, terminals, nonterminals):
                        for simbolo in follows[A]:
                            if add_unique(simbolo, follows[B]):
                                cambio = True

    return follows

def construir_tabla_reglas(reglas, primeros, siguientes, terminales, no_terminales):
    tabla_reglas = {}

    for nt in no_terminales:
        tabla_reglas[nt] = {}
        for term in terminales + ['$']:
            tabla_reglas[nt][term] = []

    for regla in reglas:
        lado_izq, lado_der = [parte.strip() for parte in regla.split('->')]
        simbolos_der = lado_der.split()

        primeros_der = obtener_first_en_secuencia(simbolos_der, primeros, terminales, no_terminales)

        for term in primeros_der:
            if term != EPSILON:
                tabla_reglas[lado_izq][term] = [regla]

        if EPSILON in primeros_der:
            for term in siguientes[lado_izq]:
                tabla_reglas[lado_izq][term] = [regla]

    for nt in no_terminales:
        for term in terminales + ['$']:
            if not tabla_reglas[nt][term]:
                if term in siguientes[nt] or term == '$':
                    tabla_reglas[nt][term] = ['EXT']
                else:
                    tabla_reglas[nt][term] = ['EXP']

    return tabla_reglas

def analizar_entrada(cadena_entrada, tabla_reglas, simbolo_inicial, terminales, no_terminales, siguientes):

    pila = ['$', simbolo_inicial]
    tokens = cadena_entrada.split() + ['$']
    apuntador = 0
    pasos = []
    contador_errores = 0
    max_errores = 5

    while len(pila) > 0 and contador_errores < max_errores:
        tope = pila[-1]
        token_actual = tokens[apuntador]

        info_paso = {
            'Paso': len(pasos) + 1,
            'Pila': ' '.join(pila),
            'Entrada': ' '.join(tokens[apuntador:]),
            'Acción': ''
        }

        if tope == token_actual == '$':
            info_paso['Acción'] = "ACEPTAR"
            pasos.append(info_paso)
            break

        elif tope == token_actual:
            info_paso['Acción'] = f"MATCH: {tope}"
            pila.pop()
            apuntador += 1

        elif tope in terminales:
            info_paso['Acción'] = f"ERROR: Se esperaba {tope}, se encontró {token_actual}"
            pasos.append(info_paso)
            apuntador += 1
            contador_errores += 1
            continue

        else:
            if token_actual in tabla_reglas[tope]:
                accion = tabla_reglas[tope][token_actual][0]

                if accion == 'EXT':
                    info_paso['Acción'] = f"EXTRAER: Sacar {tope} (sincronización)"
                    pila.pop()
                    contador_errores += 1

                elif accion == 'EXP':
                    info_paso['Acción'] = f"EXPLORAR: Saltar {token_actual}"
                    apuntador += 1
                    contador_errores += 1

                else:
                    partes = accion.split('->')
                    lado_der = partes[1].strip().split()
                    pila.pop()
                    if lado_der[0] != EPSILON:
                        for simbolo in reversed(lado_der):
                            pila.append(simbolo)
                    info_paso['Acción'] = f"Expandir: {accion}"
            else:
                if token_actual in siguientes[tope] or token_actual == '$':
                    info_paso['Acción'] = f"EXTRAER: Sacar {tope} (sincronización)"
                    pila.pop()
                else:
                    info_paso['Acción'] = f"EXPLORAR: Saltar {token_actual}"
                    apuntador += 1
                contador_errores += 1

        pasos.append(info_paso)

    df_pasos = pd.DataFrame(pasos)

    st.markdown("### 📋 Pasos del Análisis")

    if contador_errores > 0:
      st.warning(f"⚠️ Se encontraron {contador_errores} errores durante el análisis")
    st.dataframe(df_pasos[['Paso', 'Pila','Entrada','Acción' ]], use_container_width=True)
    return contador_errores == 0 and pasos[-1]['Acción'] == "ACEPTAR"

def main():
    st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .stTextArea textarea {
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        .stCodeBlock {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .success-box {
            border-left: 5px solid #2ecc71;
            padding: 1rem;
            background-color: #f0fff4;
            border-radius: 5px;
        }
        .error-box {
            border-left: 5px solid #e74c3c;
            padding: 1rem;
            background-color: #fff0f0;
            border-radius: 5px;
        }
        .transform-box {
            border-left: 5px solid #3498db;
            padding: 1rem;
            background-color: #f0f8ff;
            border-radius: 5px;
        }
        .header {
            color: #2c3e50;
            font-weight: 700;
        }
        .stButton>button {
            background-color: #3498db;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    colored_header(
        label="LL(1) Analyzer Pro",
        description="Herramienta para análisis y transformación de gramaticas que no son LL(1) a LL(1)",
        color_name="blue-70"
    )

    instruction_card = card(
        title="📋 Instrucciones",
        text="Siga estos pasos para analizar su gramática:",
        styles={
            "card": {
                "width": "100%",
                "padding": "20px",
                "background": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)"
            }
        }
    )
    st.markdown("""
    1. Ingrese su gramática en el área de texto (una producción por línea)
    2. Separe alternativas con el símbolo `ε`
    3. Haga clic en **Analizar Gramática**
    4. Revise los resultados y transformaciones sugeridas
    5. Cada token de los inputs debe de estar separado por un espacio.
    6. La cadena vacia es representado por Epsilon (ε). Puedes copiar el simbolo y reemplazar donde este tu cadena vacia.
    """)
    col1, col2 = st.columns([2, 1], gap="large")

    with col1:

        components.html("""
              <button onclick="navigator.clipboard.writeText('ε')"
                      style="padding: 0.5em 1em; font-size: 16px; background-color: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer;">
                  📋 Copiar símbolo ε al portapapeles
              </button>
              <script>
                  const btn = document.querySelector('button');
                  btn.addEventListener('click', () => {
                      btn.innerText = "✔ Copiado!";
                      setTimeout(() => btn.innerText = "📋 Copiar símbolo ε al portapapeles", 2000);
                  });
              </script>
          """, height=70)

        with stylable_container(
            
            key="grammar_input",
            css_styles="""
            {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 10px;
                padding: 1rem;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            """
        ):
            st.markdown("### ✍️ Editor de Gramática")
            grammar = st.text_area(
                "Ingrese su gramática aquí:",
                value=st.session_state.grammar_input,
                height=300,
                label_visibility="collapsed",
                placeholder="Ejemplo:\nE -> E + T | T\nT -> T * F | F\nF -> ( E ) | id"
            )
            if "cadena" not in st.session_state:
                st.session_state.cadena = ""

            cadena_input = st.text_area(
                "Ingrese la cadena a analizar (ej: id + id * id):",
                value=st.session_state.cadena,
                height=200,
                label_visibility="collapsed",
                placeholder="id + id * id"
                )

        if st.button("🔍 Analizar Gramática", type="primary", use_container_width=True):
            with st.spinner("Analizando gramática..."):
                time.sleep(1)
                rules = [r.strip() for r in grammar.splitlines() if r.strip()]
                st.session_state.grammar_input = grammar
                st.session_state.cadena = cadena_input
                cadena_input = cadena_input
                nonterms = procesamiento_gramatica(rules)
                if is_ll1(rules, nonterms):
                  with stylable_container(
                      key="success_container",
                      css_styles="""
                      {
                          border-radius: 10px;
                          padding: 1rem;
                          background-color: #000000;
                          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                      }
                      """
                  ):
                      st.success("✅ **La gramática ES LL(1)**")

                      alfabeto, no_terminales, terminales = proccess_ll1(rules)

                      primeros = obtener_firsts(rules, no_terminales, terminales)

                      siguientes = obtener_los_follows(rules, no_terminales, primeros, terminales)

                      tabla_reglas = construir_tabla_reglas(rules, primeros, siguientes, terminales, no_terminales)


                      st.session_state.es_ll1 = True
                      st.session_state.rules = rules
                      st.session_state.no_terminales = no_terminales
                      st.session_state.terminales = terminales
                      st.session_state.primeros = primeros
                      st.session_state.siguientes = siguientes
                      st.session_state.tabla_reglas = tabla_reglas

                      with st.expander("Conjuntos FIRST", expanded=True):
                          firsts_data = {nt: ', '.join(primeros[nt]) for nt in primeros}
                          df_firsts = pd.DataFrame.from_dict(firsts_data, orient='index', columns=['FIRST'])
                          st.dataframe(df_firsts)

                      with st.expander("Conjuntos FOLLOW", expanded=True):
                          follows_data = {nt: ', '.join(siguientes[nt]) for nt in siguientes}
                          df_follows = pd.DataFrame.from_dict(follows_data, orient='index', columns=['FOLLOW'])
                          st.dataframe(df_follows)

                      st.subheader("Tabla de Análisis LL(1)")
                      tabla_data = {}
                      for nt in tabla_reglas:
                          tabla_data[nt] = {}
                          for term in terminales + ['$']:
                              if term in tabla_reglas[nt]:
                                  content = ' | '.join(tabla_reglas[nt][term])
                                  tabla_data[nt][term] = content
                              else:
                                  tabla_data[nt][term] = ''

                      df_tabla = pd.DataFrame(tabla_data).T
                      st.dataframe(df_tabla)
                      st.markdown("---")
                      st.subheader("Analizador de Cadenas")
                      st.markdown("### Resultado del Análisis")
                      resultado = analizar_entrada(cadena_input, tabla_reglas, no_terminales[0], terminales, no_terminales, siguientes)
                      if resultado:
                          st.success("✅ **La cadena es ACEPTADA por la gramática**")
                          st.balloons()
                      else:
                          st.error("❌ **La cadena es RECHAZADA por la gramática**")


                else:
                    with stylable_container(
                        key="error_container",
                        css_styles="""
                        {
                            border-radius: 10px;
                            padding: 1rem;
                            background-color: #000000;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        }
                        """
                    ):
                        st.error("❌ **La gramática NO ES LL(1)**")

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for percent in range(0, 101, 20):
                            status_text.text(f"Transformando a LL(1)... {percent}%")
                            progress_bar.progress(percent)
                            time.sleep(0.2)
                        r = tiene_recursion_por_izquierda(rules,nonterms)
                        f = tiene_factorizacion_por_izquierda(rules,nonterms)
                        transformed, steps = transformar_a_ll1(rules, nonterms, r,f)
                        st.session_state.transformed_grammar = '\n'.join(transformed)
                        st.session_state.conversion_steps = steps

                        progress_bar.empty()
                        status_text.empty()

                        with stylable_container(
                            key="transform_container",
                            css_styles="""
                            {
                                border-radius: 10px;
                                padding: 1rem;
                                background-color: #000000;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            }
                            """
                        ):
                            st.success("✨ **Gramática transformada a LL(1):**")
                            st.code(st.session_state.transformed_grammar, language="bnf")

                            with st.expander("📝 **Ver pasos detallados de transformación**", expanded=False):
                                for i, step in enumerate(st.session_state.conversion_steps, 1):
                                    st.markdown(f"{i}. {step}")

                        alfabeto, no_terminales, terminales = proccess_ll1(transformed)

                        primeros = obtener_firsts(transformed, no_terminales, terminales)

                        siguientes = obtener_los_follows(transformed, no_terminales, primeros, terminales)

                        tabla_reglas = construir_tabla_reglas(transformed, primeros, siguientes, terminales, no_terminales)


                        st.session_state.es_ll1 = True
                        st.session_state.rules = transformed
                        st.session_state.no_terminales = no_terminales
                        st.session_state.terminales = terminales
                        st.session_state.primeros = primeros
                        st.session_state.siguientes = siguientes
                        st.session_state.tabla_reglas = tabla_reglas

                        with st.expander("Conjuntos FIRST", expanded=True):
                            firsts_data = {nt: ', '.join(primeros[nt]) for nt in primeros}
                            df_firsts = pd.DataFrame.from_dict(firsts_data, orient='index', columns=['FIRST'])
                            st.dataframe(df_firsts)

                        with st.expander("Conjuntos FOLLOW", expanded=True):
                            follows_data = {nt: ', '.join(siguientes[nt]) for nt in siguientes}
                            df_follows = pd.DataFrame.from_dict(follows_data, orient='index', columns=['FOLLOW'])
                            st.dataframe(df_follows)

                        st.subheader("Tabla de Análisis LL(1)")
                        tabla_data = {}
                        for nt in tabla_reglas:
                            tabla_data[nt] = {}
                            for term in terminales + ['$']:
                                if term in tabla_reglas[nt]:
                                    content = ' | '.join(tabla_reglas[nt][term])
                                    tabla_data[nt][term] = content
                                else:
                                    tabla_data[nt][term] = ''

                        df_tabla = pd.DataFrame(tabla_data).T
                        st.dataframe(df_tabla)
                        st.markdown("---")
                        st.subheader("Analizador de Cadenas")
                        st.markdown("### Resultado del Análisis")
                        resultado = analizar_entrada(cadena_input, tabla_reglas, no_terminales[0], terminales, no_terminales, siguientes)
                        if resultado:
                            st.success("✅ **La cadena es ACEPTADA por la gramática**")
                            st.balloons()
                        else:
                            st.error("❌ **La cadena es RECHAZADA por la gramática**")

    with col2:
        with stylable_container(
            key="info_panel",
            css_styles="""
            {
                border-radius: 10px;
                padding: 1.5rem;
                background-color: black;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            """
        ):
            st.markdown("### ℹ️ Información LL(1)")
            st.markdown("""
            Una gramática es **LL(1)** si:

            - No tiene **recursión por izquierda**
            - No necesita **factorización por izquierda**
            - No tiene **ambigüedades** en la tabla de análisis

            **Ejemplo válido:**
            ```bnf
            S -> aB
            B -> bC | ε
            C -> c
            ```

            **Ejemplo no válido:**
            ```bnf
            E -> E + T | T  # Recursión izquierda
            T -> id | id T  # Necesita factorización
            ```
            """)

        author_card = card(
            title="👨‍💻 Autores: ",
            text="""Desarrollado por:
              - Matias Meneses, Zamir Lizardo y Hector Nieto
          
            """,
            styles={
                "card": {
                    "width": "100%",
                    "margin-top": "20px",
                    "padding": "20px",
                    "background": "linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%)"
                }
            }
        )


if __name__ == "__main__":
    inicializacion()
    main()