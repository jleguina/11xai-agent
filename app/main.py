import io
import sys
import time

import streamlit as st

from app.agent import init_agent_executor
from app.tools import HRPolicyEmailTool, RespondTool, WelcomeEmailTool


class CaptureStdout:
    def __init__(self):
        self.new_stdout = io.StringIO()
        self.old_stdout = sys.stdout

    def __enter__(self):
        sys.stdout = self.new_stdout
        return self

    def __exit__(self, *args):
        self.value = self.new_stdout.getvalue()
        self.new_stdout.close()
        sys.stdout = self.old_stdout

    def getvalue(self):
        return self.value.strip()


if __name__ == """__main__""":
    st.title("ChatGPT-like clone")

    #  Add a debug mode to show the logs
    debug = st.checkbox("Debug mode")
    st.session_state.debug = debug

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi, I am Maria, your personal HR assistant. To get started, can you please tell me your name and email address? Thanks!",
            }
        ]
        st.session_state.debug_logs = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("What's up?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        tools = [RespondTool(), WelcomeEmailTool(), HRPolicyEmailTool()]

        agent_executor = init_agent_executor(tools, verbose=True)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            with st.spinner("Thinking..."):
                # TODO - manage conversation history length
                # Capture the stdout
                with CaptureStdout() as c:
                    llm_output = agent_executor.invoke(
                        {
                            "input": user_input,
                            "chat_history": st.session_state.messages[:-1],
                        }
                    )["output"]

            st.session_state.debug_logs.append(c.getvalue())

            for response in llm_output:
                full_response += response
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)

            message_placeholder.markdown(full_response)
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
