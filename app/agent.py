from pathlib import Path

from langchain.agents import AgentExecutor, Tool, ZeroShotAgent
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import load_prompt

from app.config import settings
from app.output_parser import CustomJSONOutputParser

tools = [
    Tool(
        name="final_answer",
        func=lambda: print("skdfjksdfjklsjdlkfjslkdfjlskdjfl"),
        description="used to give the final answer to the human. The input to this tool is a string with the answer",
    ),
]

prompt = load_prompt(Path("./app/prompts/master.yaml").resolve())
tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
tool_names = ", ".join([tool.name for tool in tools])
prompt = prompt.partial(tool_names=tool_names, tool_strings=tool_strings)

llm = ChatOpenAI(temperature=0, model=settings.OPENAI_MODEL)
llm_chain = LLMChain(llm=llm, prompt=prompt)

agent = ZeroShotAgent(
    llm_chain=llm_chain,
    allowed_tools=[tool.name for tool in tools],
    output_parser=CustomJSONOutputParser(),
)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True),
)


agent_executor.invoke({"input": "Hello, I am a Jeff."})["output"]


agent_executor.invoke({"input": "what is my name?"})["output"]
