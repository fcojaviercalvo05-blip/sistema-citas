import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
CORS(app)  # Permite peticiones desde Netlify

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")

def get_sheet():
    if os.path.exists(CREDENTIALS_PATH):
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    else:
        creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    
    client = gspread.authorize(creds)
    
    # Abrir la hoja por su nombre completo y seleccionar la pestaña 'Control de Citas'
    sheet = client.open("Control de Citas y Prospectos Diario").worksheet("Control de Citas")
    return sheet

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "active", "message": "Servidor de Citas en línea"}), 200

# 1. GUARDAR NUEVA CITA
@app.route("/guardar-cita", methods=["POST"])
def guardar_cita():
    try:
        data = request.json
        sheet = get_sheet()
        
        # Obtener todos los valores de la columna A (IDs) para calcular el siguiente ID
        col_ids = sheet.col_values(1)
        
        # Los IDs numéricos empiezan en la fila 5
        ids_numericos = []
        for val in col_ids[4:]:  # omitir filas 1, 2, 3 y 4 (encabezados)
            if val.isdigit():
                ids_numericos.append(int(val))
                
        next_id = max(ids_numericos) + 1 if ids_numericos else 1
        
        nueva_fila = [
            next_id,
            data.get("fecha", ""),
            data.get("horario", ""),
            data.get("vendedor", ""),
            data.get("prospecto", ""),
            data.get("telefono", ""),
            data.get("medio", ""),
            data.get("producto", ""),
            data.get("resultado", ""),
            data.get("observaciones", "")
        ]
        
        sheet.append_row(nueva_fila)
        return jsonify({"status": "success", "id": next_id}), 200
    except Exception as e:
        print(f"Error en guardar_cita: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 2. BUSCAR CITA POR ID
@app.route("/obtener-cita/<cita_id>", methods=["GET"])
def obtener_cita(cita_id):
    try:
        sheet = get_sheet()
        
        # Buscar en la primera columna (Columna A - ID Cita)
        try:
            cell = sheet.find(str(cita_id), in_column=1)
        except gspread.exceptions.CellNotFound:
            cell = None

        if not cell:
            return jsonify({"status": "error", "message": f"No se encontró ninguna cita con el ID '{cita_id}'"}), 404
        
        row_values = sheet.row_values(cell.row)
        
        def get_val(idx):
            return row_values[idx] if idx < len(row_values) else ""

        cita = {
            "id": get_val(0),
            "fecha": get_val(1),
            "horario": get_val(2),
            "vendedor": get_val(3),
            "prospecto": get_val(4),
            "telefono": get_val(5),
            "medio": get_val(6),
            "producto": get_val(7),
            "resultado": get_val(8),
            "observaciones": get_val(9)
        }
        
        return jsonify({"status": "success", "data": cita}), 200
    except Exception as e:
        print(f"Error en obtener_cita: {e}")
        return jsonify({"status": "error", "message": f"Error interno: {str(e)}"}), 500

# 3. ACTUALIZAR CITA EXISTENTE POR ID
@app.route("/actualizar-cita", methods=["POST"])
def actualizar_cita():
    try:
        data = request.json
        cita_id = str(data.get("id", "")).strip()
        
        if not cita_id:
            return jsonify({"status": "error", "message": "ID de cita requerido para actualizar"}), 400
            
        sheet = get_sheet()
        
        try:
            cell = sheet.find(cita_id, in_column=1)
        except gspread.exceptions.CellNotFound:
            cell = None
        
        if not cell:
            return jsonify({"status": "error", "message": f"No se encontró la cita con ID '{cita_id}' para actualizar"}), 404
            
        row_num = cell.row
        
        fila_actualizada = [
            cita_id,
            data.get("fecha", ""),
            data.get("horario", ""),
            data.get("vendedor", ""),
            data.get("prospecto", ""),
            data.get("telefono", ""),
            data.get("medio", ""),
            data.get("producto", ""),
            data.get("resultado", ""),
            data.get("observaciones", "")
        ]
        
        # Actualiza el rango A:J en la fila exacta encontrada
        sheet.update(f"A{row_num}:J{row_num}", [fila_actualizada])
        
        return jsonify({"status": "success", "message": f"Cita ID {cita_id} actualizada correctamente"}), 200
    except Exception as e:
        print(f"Error en actualizar_cita: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
