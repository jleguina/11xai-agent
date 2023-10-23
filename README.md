# 11xai-agent

To run the agent, do the following:
    1. Install the requirements: `poetry install`
    2. Run streamlit: `poetry run streamlit run app/main.py`


### Issues
1. Slack:
   - Problem: Adding users to a Slack workspace requires an Enterprise Grid subscription. See [here](https://api.slack.com/methods/admin.users.invite).
   - Solution: instead of using the Slack API, the agent sends an invite link via email.
