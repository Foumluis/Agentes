from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv
import mysql.connector as mysql
from typing import List, Dict, Any
from tool import toolsC
load_dotenv()

agent = Agent( 
    'google-gla:gemini-2.5-flash',
    system_prompt='You are an AI assistant designed to act as an expert interface to a database server. \
        Your primary function is to translate natural language user requests into precise, efficient SQL queries. \
        You have access to tools to explore the database schema and execute queries. \
        First use get_tables to see available tables, then get_table_schema to understand their structure. \
        If a users request is ambiguous, ask for clarification before proceeding. \
        After executing a query, present the results in a clear, summarized format.',
)

# Función auxiliar para obtener la conexión
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
    #print(cursor.fetchall()) [('areaEspecializacion',), 
    # ('areaEstudio',), ('articulo',), ('equipamiento',), ('estadoProyecto',), ('gradoAcademico',), 
    # ('institucion',), ('investigacion',), ('investigador',), ('laboratorio',), ('proyecto',), 
    # ('proyectoLaboratorio',), ('rolInvestigador',), ('tema',)]
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    conexion.close()
    return tables

@agent.tool_plain
def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """Get the schema (columns and types) of a specific table.
    
    Args:
        table_name: The name of the table to describe
    """
    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    #print(cursor.fetchall()) lab [('idLaboratorio', 'bigint unsigned', 'NO', 'PRI', None, 'auto_increment'), 
    # ('idInstitucion', 'bigint unsigned', 'NO', 'MUL', None, '')
    # , ('ubicacionFisica', 'varchar(200)', 'NO', '', None, ''), ('aforo', 'int unsigned', 'NO', '', None, '')]
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
    return columns

@agent.tool_plain
def execute_query(query: str) -> List[Dict[str, Any]]:
    """Execute any SQL query and return the results."""
    conexion = None
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        
        print(f"[DEBUG] Ejecutando: {query}")  # ← Debug
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            cursor.close()
            conexion.close()
            return results if results else [{"message": "No results"}]
        
        # Para modificaciones
        affected = cursor.rowcount
        print(f"[DEBUG] Filas afectadas: {affected}")  # ← Debug
        
        conexion.commit()
        print(f"[DEBUG] Commit realizado")  # ← Debug
        
        cursor.close()
        conexion.close()
        
        # Verificar que realmente se insertó
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

# Loop principal
historial = []
print("Chatbot de Base de Datos - Escribe 'salir' para terminar\n")

while True:
    mensaje = input('You: ')
    if mensaje.lower() == 'salir':
        break
    
    try:
        respuestaIA = agent.run_sync(mensaje, message_history=historial)
        historial = respuestaIA.new_messages()
        print(f"\nAI: {respuestaIA.output}\n")  # ← CAMBIO AQUÍ: .output en lugar de .data
    except Exception as e:
        print(f"\nError: {e}\n")
