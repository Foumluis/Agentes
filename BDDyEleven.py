from pydantic_ai import Agent
from dotenv import load_dotenv
import mysql.connector as mysql
from typing import List, Dict, Any
import os
from elevenlabs import ElevenLabs
import speech_recognition as sr
import io
import sounddevice as sd
import soundfile as sf

load_dotenv()

# Configuración del agente de base de datos
agent = Agent( 
    'google-gla:gemini-2.5-flash',
    system_prompt='You are an AI assistant designed to act as an expert interface to a database server. \
        Your primary function is to translate natural language user requests into precise, efficient SQL queries. \
        You have access to tools to explore the database schema and execute queries. \
        First use get_tables to see available tables, then get_table_schema to understand their structure. \
        If a users request is ambiguous, ask for clarification before proceeding. \
        After executing a query, present the results in a clear, summarized format. \
        Always respond in Spanish and be concise in your explanations.',
)

def get_db_connection():
    return mysql.connect(
        host="localhost",  
        user="Admin",
        password="Hola123",
        database="ia",
        autocommit=True
    )

@agent.tool_plain
def get_tables() -> List[str]:
    """Get a list of all tables in the database."""
    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    conexion.close()
    print(f"[DEBUG] Tablas: {tables}")
    return tables

@agent.tool_plain
def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """Get the schema (columns and types) of a specific table."""
    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'field': row[0],
            'type': row[1],
            'null': row[2],
            'key': row[3],
            'default': row[4],
            'extra': row[5]
        })
    cursor.close()
    conexion.close()
    print(f"[DEBUG] Schema de {table_name}: {len(columns)} columnas")
    return columns

@agent.tool_plain
def execute_query(query: str) -> List[Dict[str, Any]]:
    """Execute any SQL query and return the results."""
    conexion = None
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        
        print(f"[DEBUG] Ejecutando: {query}")
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            cursor.close()
            conexion.close()
            return results if results else [{"message": "No results"}]
        
        affected = cursor.rowcount
        conexion.commit()
        
        cursor.close()
        conexion.close()
        
        conexion2 = get_db_connection()
        cursor2 = conexion2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM LABORATORIO ORDER BY IDLABORATORIO DESC LIMIT 1")
        ultimo = cursor2.fetchone()
        cursor2.close()
        conexion2.close()
        
        return [{
            "success": True, 
            "affected_rows": affected,
            "last_inserted": ultimo
        }]
        
    except Exception as e:
        if conexion:
            conexion.rollback()
            conexion.close()
        return [{"error": str(e), "query": query}]

historial = []

# Inicializar cliente de ElevenLabs
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def escuchar_microfono():
    """Escucha el micrófono y transcribe"""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.pause_threshold = 1.5
    recognizer.dynamic_energy_threshold = True
    
    with sr.Microphone() as source:
        print("\n🎤 Escuchando... (habla ahora)")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        
        try:
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=15)
            print("🔄 Procesando...")
            
            texto = recognizer.recognize_google(audio, language="es-ES")
            return texto
            
        except sr.UnknownValueError:
            print("❌ No pude entender lo que dijiste")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

def hablar(texto):
    """Convierte texto a voz con ElevenLabs"""
    try:
        # Generar el audio con ElevenLabs
        audio_generator = client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
            text=texto,
            model_id="eleven_multilingual_v2",
        )
        
        # Convertir el generador a bytes
        audio_bytes = b"".join(audio_generator)
        
        # Reproducir usando sounddevice
        audio_io = io.BytesIO(audio_bytes)
        data, samplerate = sf.read(audio_io)
        sd.play(data, samplerate)
        sd.wait()  # Esperar a que termine de reproducir
        
    except Exception as e:
        print(f"Error al hablar: {e}")
        import traceback
        traceback.print_exc()

def main():
    global historial
    
    print("=== Chatbot de Base de Datos con Voz ===")
    print("Di 'salir' para terminar\n")
    
    # Saludo inicial
    saludo = "Hola, soy tu asistente de base de datos. ¿En qué puedo ayudarte?"
    print(f"🤖 {saludo}")
    hablar(saludo)
    
    while True:
        try:
            # Escuchar al usuario
            texto_usuario = escuchar_microfono()
            
            if texto_usuario is None:
                continue
                
            print(f"👤 Tú: {texto_usuario}")
            
            # Verificar si quiere salir
            if any(palabra in texto_usuario.lower() for palabra in ['salir', 'adiós', 'chao', 'terminar']):
                despedida = "Hasta luego, que tengas un buen día"
                print(f"🤖 {despedida}")
                hablar(despedida)
                break
            
            # Procesar con Pydantic AI
            print("[DEBUG] Procesando con Pydantic AI...")
            respuesta_ia = agent.run_sync(texto_usuario, message_history=historial)
            historial = respuesta_ia.new_messages()
            respuesta = respuesta_ia.output
            
            print(f"🤖 {respuesta}\n")
            
            # Hablar la respuesta
            hablar(respuesta)
            
        except KeyboardInterrupt:
            print("\n\n👋 Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error general: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()