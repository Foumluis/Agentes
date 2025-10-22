import requests
from pydantic_ai import Agent
from dotenv import load_dotenv
import asyncio

load_dotenv()
agent = Agent(  
    'google-gla:gemini-2.5-flash',
    instructions='Be concise, reply with a one sentence, and search in internet',  
)



@agent.tool_plain
def get_weather_info (latitude:float,longitude:float)->str:
    print(f"Viendo el tiempo para {latitude}, {longitude}")
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature-2m,weather_code"
    respuesta = requests.get(url)
    return respuesta.json()
historial = []
while True:
    mensaje =input('You: ')
    if mensaje == 'salir':
        break
    respuestaIA = agent.run_sync(mensaje,message_history=historial)
    historial = respuestaIA.new_messages()
    print(respuestaIA.output)