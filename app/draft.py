import multiprocessing
import time
from dataclasses import dataclass

import streamlit as st
from langchain.agents import AgentExecutor

from app.agent.executor import init_agent_executor
from app.agent.tools import RespondTool, WelcomeEmailTool


def llm_execution(shared_dict):
    # Your LLM execution and callback goes here
    # In this example, I'll just assign a value to the shared dictionary:
    shared_dict["welcome_email_sent"] = True
    time.sleep(15)
    shared_dict["result"] = shared_dict["user_input"] + " - response from LLM"


@dataclass
class RoleType:
    USER = "user"
    ASSISTANT = "assistant"


class MariaApp:
    def __init__(self) -> None:
        if "messages" not in st.session_state:
            self.init_session_state()

        if "process" not in st.session_state:
            self.init_subprocess_manager()

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

        # Onboarding status
        st.session_state.welcome_email_sent = False

    def init_subprocess_manager(self) -> None:
        manager = multiprocessing.Manager()
        shared_dict = manager.dict()

        shared_dict["welcome_email_sent"] = False
        shared_dict["user_input"] = None
        shared_dict["result"] = None

        st.session_state.shared_dict = shared_dict
        st.session_state.process = multiprocessing.Process(
            target=llm_execution, args=(shared_dict,)
        )

    def onboarding_status_widget(self) -> None:
        with st.expander("Onboarding Status", expanded=True):
            st.checkbox(
                "Welcome Email",
                value=st.session_state.shared_dict["welcome_email_sent"],
                disabled=True,
            )

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
                - Make and edit time off requests.
                - Estimate your remaining time off balance.
                """
            )

            st.markdown("<br>", unsafe_allow_html=True)

            self.onboarding_progress_container = st.container()
            with self.onboarding_progress_container:
                self.onboarding_status_widget()

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

    def init_agent(self) -> AgentExecutor:
        # Status callbacks
        def set_welcome_email_status():
            st.session_state.welcome_email_sent = True
            st.rerun()

        tools = [RespondTool(), WelcomeEmailTool(callback=set_welcome_email_status)]
        return init_agent_executor(tools, verbose=True)

    def handle_chat_input(self) -> None:
        if user_input := st.chat_input("What's up?"):
            # Count the number of words in the user input
            num_words = len(user_input.split())
            if num_words > 500:
                st.error("Please keep your message under 500 words.")
                return

            self.store_message(RoleType.USER, user_input)

            with st.chat_message(RoleType.USER):
                st.markdown(user_input)

            # agent_executor = self.init_agent()

            st.session_state.shared_dict["user_input"] = user_input
            st.session_state.process.start()
            st.spinner("Thinking...")

    def run(self) -> None:
        st.title("Talk to me!")

        self.sidebar()
        self.render_chat()
        self.handle_chat_input()

        if st.session_state.process.is_alive():
            st.spinner("Thinking...")
            st.rerun()

        if (
            "process" in st.session_state
            and not st.session_state.process.is_alive()
            and st.session_state.shared_dict["result"]
        ):
            st.session_state.process.join()
            with st.chat_message(RoleType.ASSISTANT):
                message_placeholder = st.empty()
                full_response = ""

                for response in st.session_state.shared_dict.pop("result"):
                    full_response += response
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.02)

                message_placeholder.markdown(full_response)
            self.store_message(RoleType.ASSISTANT, full_response)

            # Reset process manager
            manager = multiprocessing.Manager()
            shared_dict = manager.dict()

            shared_dict["welcome_email_sent"] = st.session_state.shared_dict[
                "welcome_email_sent"
            ]
            shared_dict["user_input"] = None
            shared_dict["result"] = None

            st.session_state.shared_dict = shared_dict
            st.session_state.process = multiprocessing.Process(
                target=llm_execution, args=(shared_dict,)
            )


if __name__ == "__main__":
    MariaApp().run()
