from pydantic_ai import Agent

from dotenv import load_dotenv


load_dotenv()
agent = Agent(  
    'google-gla:gemini-2.5-flash',
    instructions='Be concise, reply with one sentence.',  
)

result = agent.run_sync('explicame como nacio git    ')  
print(result.output)
