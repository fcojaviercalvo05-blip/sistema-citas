import os
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
        # Fallback si se usa variable de entorno
        import json
        creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    
    client = gspread.authorize(creds)
    # Reemplaza si tu hoja tiene un nombre exacto diferente
    sheet = client.open_by_key("TU_SPREADSHEET_ID_AQUI").sheet1 
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
        records = sheet.get_all_records()
        
        # Calcular siguiente ID
        next_id = len(records) + 1
        
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
        return jsonify({"status": "error", "message": str(e)}), 500

# 2. BUSCAR CITA POR ID
@app.route("/obtener-cita/<int:cita_id>", methods=["GET"])
def obtener_cita(cita_id):
    try:
        sheet = get_sheet()
        cell = sheet.find(str(cita_id), in_column=1)
        
        if not cell:
            return jsonify({"status": "error", "message": f"No se encontró la cita con ID {cita_id}"}), 404
        
        row_values = sheet.row_values(cell.row)
        
        cita = {
            "id": row_values[0] if len(row_values) > 0 else "",
            "fecha": row_values[1] if len(row_values) > 1 else "",
            "horario": row_values[2] if len(row_values) > 2 else "",
            "vendedor": row_values[3] if len(row_values) > 3 else "",
            "prospecto": row_values[4] if len(row_values) > 4 else "",
            "telefono": row_values[5] if len(row_values) > 5 else "",
            "medio": row_values[6] if len(row_values) > 6 else "",
            "producto": row_values[7] if len(row_values) > 7 else "",
            "resultado": row_values[8] if len(row_values) > 8 else "",
            "observaciones": row_values[9] if len(row_values) > 9 else ""
        }
        
        return jsonify({"status": "success", "data": cita}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 3. ACTUALIZAR CITA EXISTENTE POR ID
@app.route("/actualizar-cita", methods=["POST"])
def actualizar_cita():
    try:
        data = request.json
        cita_id = str(data.get("id"))
        
        if not cita_id:
            return jsonify({"status": "error", "message": "ID de cita requerido"}), 400
            
        sheet = get_sheet()
        cell = sheet.find(cita_id, in_column=1)
        
        if not cell:
            return jsonify({"status": "error", "message": f"No se encontró la cita con ID {cita_id}"}), 404
            
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
        
        # Actualiza el rango completo de la fila (A:J)
        sheet.update(f"A{row_num}:J{row_num}", [fila_actualizada])
        
        return jsonify({"status": "success", "message": f"Cita ID {cita_id} actualizada correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
