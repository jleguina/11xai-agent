from pathlib import Path

from langchain.agents import AgentExecutor, ZeroShotAgent
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import load_prompt
from langchain.tools import BaseTool

from app.config import settings
from app.output_parser import CustomJSONOutputParser
from app.tools import WelcomeEmailTool


def init_agent_executor(tools: list[BaseTool], verbose=False) -> AgentExecutor:
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
        agent=agent, tools=tools, handle_parsing_errors=True, verbose=verbose
    )

    return agent_executor


if __name__ == "__main__":
    chat_history = []
    tools = [WelcomeEmailTool()]

    agent_executor = init_agent_executor(tools)

    init_message = "Hi, I am test agent, what can I do for you?"
    print("Agent: Hi, I am test agent, what can I do for you?")
    chat_history.append({"role": "assistant", "content": init_message})

    while True:
        user_input = input(">>> ")
        out = agent_executor.invoke(
            {"input": user_input, "chat_history": chat_history}
        )["output"]
        print("Agent:", out)

        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": out})
