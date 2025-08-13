# Integrations

## Slack Bot
- `integrations/slack_bot/` — mention the bot and ask a question. It calls Cloud Run `/ask`.

## Teams Relay
- `integrations/teams_webhook/` — POST `{"question":"..."}` to `/relay`; it calls `/ask` and posts to Teams.

## Streamlit UI
- `rag_talk_to_your_data/ui/` — a simple web UI for the module.
