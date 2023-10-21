import time
from pathlib import Path

import streamlit as st
from langchain.agents import AgentExecutor, Tool, ZeroShotAgent
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import load_prompt

from app.config import settings
from app.output_parser import CustomJSONOutputParser


def init_agent_executor() -> AgentExecutor:
    tools = [
        Tool(
            name="final_answer",
            func=lambda: "1",
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

    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools)

    return agent_executor


if __name__ == """__main__""":
    st.title("ChatGPT-like clone")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("What's up?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        agent_executor = init_agent_executor()

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            with st.spinner("Generating response..."):
                # TODO - manage conversation history length
                llm_output = agent_executor.invoke(
                    {
                        "input": user_input,
                        "chat_history": st.session_state.messages[:-1],
                    }
                )["output"]

            for response in llm_output:
                full_response += response
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)

            message_placeholder.markdown(full_response)
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
