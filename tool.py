from elevenlabs.conversational_ai.conversation import ClientTools
import mysql.connector as mysql

def get_db_connection():
    return mysql.connect(
        host="localhost",  
        user="Admin",
        password="Hola123",
        database="ia",
        autocommit=True
    )


def get_tables(*args, **kwargs):
    """Returns a list of all table names in the database. This function requires no parameters."""
    print(f"[DEBUG get_tables] Llamada recibida")
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        conexion.close()
        
        result = ", ".join(tables) if tables else "No tables found"
        print(f"[DEBUG get_tables] Devolviendo: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[DEBUG get_tables] Error: {error_msg}")
        return error_msg


def get_table_schema(table_name=None, *args, **kwargs):
    """Get the schema (columns and types) of a specific table.
    
    Args:
        table_name: The name of the table to describe (required)
    """
    # Si table_name es un dict, extraer el valor real
    if isinstance(table_name, dict):
        table_name = table_name.get('table_name')
    
    if not table_name:
        table_name = kwargs.get('table_name')
    
    print(f"[DEBUG get_table_schema] table_name: {table_name}")
    
    if not table_name:
        return "Error: Please provide the table name as a parameter"
    
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor()
        cursor.execute(f"DESCRIBE `{table_name}`")

        columns = []
        for row in cursor.fetchall():
            columns.append(f"{row[0]} ({row[1]})")
        
        cursor.close()
        conexion.close()
        
        result = f"Table '{table_name}' has {len(columns)} columns: " + ", ".join(columns)
        print(f"[DEBUG get_table_schema] Devolviendo: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Error getting schema for table '{table_name}': {str(e)}"
        print(f"[DEBUG get_table_schema] Error: {error_msg}")
        return error_msg


def execute_query(query=None, *args, **kwargs):
    """Execute a SQL query and return the results.
    
    Args:
        query: The SQL query to execute (required)
    """
    print(f"[DEBUG execute_query] Recibido - query: {query}, type: {type(query)}")
    
    # CLAVE: Si query es un diccionario, extraer el SQL del campo 'query'
    actual_query = None
    
    if isinstance(query, dict):
        actual_query = query.get('query')
        print(f"[DEBUG execute_query] Extraído del dict: {actual_query}")
    elif isinstance(query, str):
        actual_query = query
    else:
        # Intentar obtener de kwargs
        actual_query = kwargs.get('query')
    
    print(f"[DEBUG execute_query] Query final: {actual_query}")
    
    if not actual_query:
        return "Error: No SQL query provided. Please provide a valid SQL statement."
    
    if not isinstance(actual_query, str):
        return f"Error: Query must be a string, got {type(actual_query)}"
    
    conexion = None
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        
        print(f"[DEBUG] Ejecutando SQL: {actual_query}")
        cursor.execute(actual_query)
        
        # Detectar tipo de query
        query_upper = actual_query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            results = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if not results:
                return "Query executed successfully. No results found."
            
            result_text = f"Found {len(results)} results:\n"
            for i, row in enumerate(results[:10], 1):
                result_text += f"{i}. {', '.join(f'{k}: {v}' for k, v in row.items())}\n"
            
            if len(results) > 10:
                result_text += f"... and {len(results) - 10} more results"
            
            print(f"[DEBUG execute_query] Devolviendo {len(results)} resultados")
            return result_text
        
        # Para CREATE TABLE, INSERT, UPDATE, DELETE, etc.
        affected = cursor.rowcount
        conexion.commit()
        cursor.close()
        conexion.close()
        
        # Mensaje específico para CREATE TABLE
        if query_upper.startswith('CREATE'):
            result = f"Table created successfully!"
        elif query_upper.startswith('DROP'):
            result = f"Table dropped successfully!"
        elif query_upper.startswith('INSERT'):
            result = f"Data inserted successfully. {affected} rows affected."
        elif query_upper.startswith('UPDATE'):
            result = f"Data updated successfully. {affected} rows affected."
        elif query_upper.startswith('DELETE'):
            result = f"Data deleted successfully. {affected} rows affected."
        else:
            result = f"Query executed successfully. {affected} rows affected."
        
        print(f"[DEBUG execute_query] {result}")
        return result
        
    except Exception as e:
        if conexion:
            conexion.rollback()
            conexion.close()
        error_msg = f"Error executing query: {str(e)}"
        print(f"[DEBUG execute_query] Error: {error_msg}")
        return error_msg


toolsC = ClientTools()

toolsC.register("get_tables", get_tables)
toolsC.register("get_table_schema", get_table_schema)
toolsC.register("execute_query", execute_query)