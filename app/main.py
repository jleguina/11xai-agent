import io
import re
import sys
import time
from typing import Any

import streamlit as st

from app.agent import init_agent_executor
from app.tools import get_all_tools


def no_ansi_string(ansi_string: str) -> str:
    ansi_escape = re.compile(r"\x1b[^m]*m")
    return ansi_escape.sub("", ansi_string)


class CaptureStdout:
    def __init__(self) -> None:
        self.new_stdout = io.StringIO()
        self.old_stdout = sys.stdout

    def __enter__(self) -> "CaptureStdout":
        sys.stdout = self.new_stdout
        return self

    def __exit__(self, *args: Any) -> None:
        self.value = self.new_stdout.getvalue()
        self.new_stdout.close()
        sys.stdout = self.old_stdout

    def getvalue(self) -> str:
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
                "content": """
                Hi, I am Maria, your personal HR assistant. To get started, can you please provide the following information:\n
                    - First Name
                    - Last Name
                    - Email Address
                    """,
                "log": [],
            }
        ]
        st.session_state.debug_logs = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["log"] and debug:
                st.write(message["log"])

    if user_input := st.chat_input("What's up?"):
        st.session_state.messages.append(
            {"role": "user", "content": user_input, "log": ""}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        tools = get_all_tools()
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

            for response in llm_output:
                full_response += response
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)

            logs = no_ansi_string(c.getvalue()).split("\n")
            logs = list(filter(None, logs))  # Remove blank lines
            st.write(logs)

            message_placeholder.markdown(full_response)
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response, "log": logs}
        )
