from pydantic_ai import Agent
from dotenv import load_dotenv
import asyncio

load_dotenv()
agent = Agent(  
    'google-gla:gemini-2.5-flash',
    instructions='Be concise, reply with a medium text.',  
)

async def main():
    async with agent.run_stream('de donde viene hello world?') as result:
        async for message in result.stream_text(delta=True):
            print(message)
asyncio.run(main())