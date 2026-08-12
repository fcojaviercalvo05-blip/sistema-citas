import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
CORS(app)

# Configuración de credenciales de Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    # Carga las credenciales desde el archivo credentials.json o desde una variable de entorno
    if os.path.exists("credentials.json"):
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    else:
        # En producción (Render), se recomienda guardar el JSON en variables de entorno
        import json
        json_creds = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
        creds = Credentials.from_service_account_info(json_creds, scopes=SCOPES)
        
    client = gspread.authorize(creds)
    
    # Nombre de tu Hoja de Cálculo en Google Sheets
    SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME", "Control de Citas y Prospectos Diario")
    
    sheet = client.open(SPREADSHEET_NAME).worksheet("Control de Citas")
    return sheet

@app.route('/', methods=['GET'])
def home():
    return "🚀 Servidor de Control de Citas activo 24/7 en la nube."

@app.route('/guardar-cita', methods=['POST'])
def guardar_cita():
    try:
        data = request.json
        sheet = get_sheet()
        
        # Obtener todas las filas para calcular el ID automático
        records = sheet.get_all_values()
        # Asumiendo encabezados en filas superiores, contamos las filas ocupadas
        # Si la fila 4 tiene los encabezados, la primera cita es fila 5 (ID = 1)
        next_id = max(1, len(records) - 3) if len(records) >= 4 else 1

        nueva_fila = [
            next_id,
            data.get('fecha', ''),
            data.get('horario', ''),
            data.get('vendedor', ''),
            data.get('prospecto', ''),
            data.get('telefono', ''),
            data.get('medio', ''),
            data.get('producto', ''),
            data.get('resultado', ''),
            data.get('observaciones', '')
        ]

        sheet.append_row(nueva_fila)

        return jsonify({"status": "success", "message": "Cita registrada en Google Sheets exitosamente", "id": next_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
