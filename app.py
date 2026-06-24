from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from preguntas import PREGUNTAS
import random

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Mapa maestro de tipos del Modelo A
MAPA_TIPOS = {
    ("NE", "TI"): "ILE (Intuitivo Lógico Extrovertido)",
    ("SI", "FE"): "SEI (Sensorial Ético Introvertido)",
    ("SE", "TI"): "SLE (Sensorial Lógico Extrovertido)",
    ("NI", "FE"): "IEI (Intuitivo Ético Introvertido)",
    ("TE", "NI"): "LIE (Lógico Intuitivo Extrovertido)",
    ("FI", "SE"): "ESI (Ético Sensorial Introvertido)",
    ("FE", "SI"): "ESE (Ético Sensorial Extrovertido)",
    ("TI", "NE"): "LII (Lógico Intuitivo Introvertido)",
    ("FE", "NI"): "EIE (Ético Intuitivo Extrovertido)",
    ("TI", "SE"): "LSI (Lógico Sensorial Introvertido)",
    ("SE", "FI"): "SEE (Sensorial Ético Extrovertido)",
    ("NI", "TE"): "ILI (Intuitivo Lógico Introvertido)",
    ("NE", "FI"): "IEE (Intuitivo Ético Extrovertido)",
    ("SI", "TE"): "SLI (Sensorial Lógico Introvertido)",
    ("TE", "SI"): "LSE (Lógico Sensorial Extrovertido)",
    ("FI", "NE"): "EII (Ético Intuitivo Introvertido)"
}

@app.route('/')
def index():
    session['progreso'] = 0
    session['respuestas'] = []
    
    # Inicializamos la memoria de la Ley de Compensación Estructural
    session['obligatorios_proxima'] = {
        "EGO": None,       # Balancea 'opcion_1' y 'opcion_2'
        "SUPER_EGO": None, # Balancea 'opcion_3' (Rol) y 'opcion_4' (Vulnerable)
        "SUPER_ID": None,  # Balancea 'opcion_5' y 'opcion_6'
        "ID": None         # Balancea 'opcion_7' y 'opcion_8'
    }
    return render_template('index.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
    progreso = session.get('progreso', 0)
    obligatorios = session.get('obligatorios_proxima', {})
    
    if progreso >= len(PREGUNTAS):
        return redirect(url_for('resultado'))
        
    pregunta_actual = PREGUNTAS[progreso]
    
    if request.method == 'POST':
        opcion_seleccionada = request.form.get('opcion')
        if opcion_seleccionada:
            session['respuestas'].append({
                "pregunta_id": pregunta_actual["id"],
                "elemento": pregunta_actual["elemento"],
                "bloque": opcion_seleccionada
            })
            session['progreso'] = progreso + 1
            return redirect(url_for('test'))

    # --- MOTOR DE ASIGNACIÓN POR MACRO-BLOQUES ---
    macro_bloques = {
        "EGO": ["opcion_1", "opcion_2"],
        "SUPER_EGO": ["opcion_3", "opcion_4"],
        "SUPER_ID": ["opcion_5", "opcion_6"],
        "ID": ["opcion_7", "opcion_8"]
    }
    
    claves_a_mostrar = []
    proximos_obligatorios = {}

    for bloque_nombre, lista_opciones in macro_bloques.items():
        # Si la pregunta anterior dejó fijada una opción por compensación de la psique
        if obligatorios.get(bloque_nombre):
            elegida = obligatorios[bloque_nombre]
            claves_a_mostrar.append(elegida)
            # El bloque ya se equilibró, la siguiente vuelta vuelve a ser libre
            proximos_obligatorios[bloque_nombre] = None
        else:
            # Si no hay obligación previa, elegimos una de las dos opciones por azar (50% / 50%)
            elegida = random.choice(lista_opciones)
            claves_a_mostrar.append(elegida)
            
            # DEJAMOS LA LEY LISTA: La opción hermana que se quedó fuera hoy, sale obligada mañana
            if elegida == "opcion_1": proximos_obligatorios["EGO"] = "opcion_2"
            elif elegida == "opcion_2": proximos_obligatorios["EGO"] = "opcion_1"
            
            elif elegida == "opcion_3": proximos_obligatorios["SUPER_EGO"] = "opcion_4"  # Salió Rol -> Obliga Vulnerable
            elif elegida == "opcion_4": proximos_obligatorios["SUPER_EGO"] = "opcion_3"  # Salió Vulnerable -> Obliga Rol
            
            elif elegida == "opcion_5": proximos_obligatorios["SUPER_ID"] = "opcion_6"
            elif elegida == "opcion_6": proximos_obligatorios["SUPER_ID"] = "opcion_5"
            
            elif elegida == "opcion_7": proximos_obligatorios["ID"] = "opcion_8"
            elif elegida == "opcion_8": proximos_obligatorios["ID"] = "opcion_7"

    # Guardamos los estados para la siguiente iteración
    session['obligatorios_proxima'] = proximos_obligatorios

    # Construimos el mapeo dinámico leyendo la clave 'opciones' de preguntas.py
    opciones_finales = []
    for clave in claves_a_mostrar:
        texto_opcion = pregunta_actual["opciones"][clave]
        opciones_finales.append((clave, texto_opcion))
        
    # Mezclamos las 4 opciones finales en pantalla para camuflar el orden visual
    random.shuffle(opciones_finales)

    return render_template('test.html', 
                           escenario=pregunta_actual["escenario"], 
                           elemento=pregunta_actual["elemento"],
                           opciones=opciones_finales, 
                           numero=progreso + 1)

@app.route('/resultado')
def resultado():
    respuestas = session.get('respuestas', [])
    if not respuestas:
        return redirect(url_for('index'))

    tabla_tipos = {tipo: 0 for tipo in MAPA_TIPOS.values()}
    puntajes_elementos = {el: 0 for el in ["NE", "TI", "NI", "TE", "FE", "FI", "SE", "SI"]}
    conteos_bloques = {f"opcion_{i}": 0 for i in range(1, 9)}

    for r in respuestas:
        elemento = r["elemento"]
        bloque = r["bloque"]
        conteos_bloques[bloque] += 1
        
        # Ponderación algorítmica por posición psíquica
        if bloque == "opcion_1": puntajes_elementos[elemento] += 4   
        elif bloque == "opcion_2": puntajes_elementos[elemento] += 3 
        elif bloque == "opcion_4": puntajes_elementos[elemento] -= 4 # Desempate drástico por vulnerabilidad
        elif bloque == "opcion_5": puntajes_elementos[elemento] -= 1 
        elif bloque == "opcion_8": puntajes_elementos[elemento] += 2 

    # Diagnóstico avanzado cruzando bloques Ego y filtros de Súper-Ego
    for (el_base, el_creative), nombre_tipo in MAPA_TIPOS.items():
        score_base = puntajes_elementos[el_base]
        score_creative = puntajes_elementos[el_creative]
        
        peso_tipo = (score_base * 2) + score_creative
        
        # Inferencia por rechazo de bloques vulnerables de la contraparte
        if nombre_tipo.startswith("EII") or nombre_tipo.startswith("IEE"):
            if puntajes_elementos["SE"] < 0 or puntajes_elementos["TI"] < 0:
                peso_tipo += 5  
                
        if nombre_tipo.startswith("ILE") or nombre_tipo.startswith("LII"):
            if puntajes_elementos["FI"] < 0:
                peso_tipo += 5

        if nombre_tipo.startswith("SLE") or nombre_tipo.startswith("LSI"):
            if puntajes_elementos["FI"] < 0 or puntajes_elementos["NE"] < 0:
                peso_tipo += 5

        tabla_tipos[nombre_tipo] = peso_tipo

    tipo_ganador = max(tabla_tipos, key=tabla_tipos.get)
    return render_template('resultado.html', tipo=tipo_ganador, conteo=conteos_bloques)

if __name__ == '__main__':
    app.run(debug=True)
