import time
from dataclasses import dataclass

import streamlit as st

from app.agent.executor import init_agent_executor
from app.agent.tools import get_all_tools
from app.utils import CaptureStdout, no_ansi_string


@dataclass
class RoleType:
    USER = "user"
    ASSISTANT = "assistant"


class MariaApp:
    def __init__(self) -> None:
        if "messages" not in st.session_state:
            self.init_session_state()

    def init_session_state(self) -> None:
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
        st.session_state.thinking = False

    def sidebar(self) -> None:
        with st.sidebar:
            st.title("Maria, your personal HR assistant")
            # Description
            st.markdown(
                """
                This is Maria, your personal HR assistant.
                She can help you with the following tasks:
                - Send a welcome email.
                - Send a copy of the HR policies via email.
                - Invite to the company Slack via email.
                - Schedule calendar events.
                - Answer questions about the company's HR policies.
                """
            )

            st.markdown("<br>", unsafe_allow_html=True)

            #  Add a debug mode to show the logs
            with st.expander("Debug mode"):
                st.warning(
                    "Toggling debug mode while the agent is thinking will cause issues."
                )
                debug = st.checkbox("Debug mode", disabled=st.session_state.thinking)
                st.session_state.debug = debug

            if st.button("Reset", use_container_width=True):
                self.init_session_state()

    def render_chat(self) -> None:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["log"] and st.session_state.debug:
                    st.write(message["log"])

    def store_message(self, role: str, content: str, log: list[str] = []) -> None:
        st.session_state.messages.append({"role": role, "content": content, "log": log})

    def handle_chat_input(self) -> None:
        if user_input := st.chat_input("What's up?"):
            self.store_message(RoleType.USER, user_input)

            with st.chat_message(RoleType.USER):
                st.markdown(user_input)

            tools = get_all_tools()
            agent_executor = init_agent_executor(tools, verbose=True)

            with st.chat_message(RoleType.ASSISTANT):
                message_placeholder = st.empty()
                full_response = ""

                with st.spinner("Thinking..."):
                    # TODO - manage conversation history length
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
                if st.session_state.debug:
                    st.write(logs)

                message_placeholder.markdown(full_response)
            self.store_message(RoleType.ASSISTANT, full_response, logs)

    def run(self) -> None:
        st.title("Talk to me!")

        self.sidebar()
        self.render_chat()
        self.handle_chat_input()


if __name__ == "__main__":
    MariaApp().run()
