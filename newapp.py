# ============================
# ✅ app.py — Streamlit Client (FastMCP 2.13.0.2)
# ============================
import asyncio
import streamlit as st
from fastmcp.client import Client  # ✅ Direct FastMCP client import
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import json
import inspect
import pandas as pd
from validator import RegistrationValidator  # ✅ Custom input validator

# ==========================================================
# ✅ Load environment variables
# ==========================================================
load_dotenv()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================================
# ✅ System prompt
# ==========================================================
SYSTEM_PROMPT = """
You are a helpful AI assistant connected to a registration MCP server.
Use your own knowledge for general questions.

When asked to register or view registrations, use the MCP tools:
  - add_registration(name, email, date)
  - view_all_registration()

Interpret user inputs flexibly (name, email, date).
Always remind the user to enter the date in format: YYYY-MM-DD.
"""

# ==========================================================
# ✅ Streamlit UI setup
# ==========================================================
st.set_page_config(page_title="🧠 MCP Registration Assistant")
st.title("🤖 Registration Assistant (FastMCP)")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "table_data" not in st.session_state:
    st.session_state.table_data = None
if "show_table" not in st.session_state:
    st.session_state.show_table = False

# Render past chat messages
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Show table if applicable
if st.session_state.show_table and st.session_state.table_data is not None:
    with st.chat_message("assistant"):
        st.success("✅ Here are all registrations:")
        st.dataframe(st.session_state.table_data)
    st.session_state.show_table = False

# User input box
user_input = st.chat_input("Ask me anything...")

# ==========================================================
# ✅ Helpers
# ==========================================================
def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif inspect.isroutine(obj):
        return f"<function {obj.__name__}>"
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)


def ensure_json_object(param_schema):
    """Ensure 'parameters' is a valid JSON object, not a string."""
    if isinstance(param_schema, str):
        try:
            param_schema = json.loads(param_schema)
        except json.JSONDecodeError:
            param_schema = {"type": "object", "properties": {}, "required": []}
    if not isinstance(param_schema, dict):
        param_schema = {"type": "object", "properties": {}, "required": []}
    return param_schema


def validate_inputs(args: dict) -> tuple[bool, str]:
    name = args.get("name", "")
    email = args.get("email", "")
    date = args.get("date", "")

    name_valid, name_msg = RegistrationValidator.validate_name(name)
    email_valid, email_msg = RegistrationValidator.validate_email(email)
    date_valid, date_msg = RegistrationValidator.validate_date_of_birth(date)

    if not name_valid:
        return False, name_msg
    if not email_valid:
        return False, email_msg
    if not date_valid:
        return False, date_msg

    return True, "✓ All inputs valid"

# ==========================================================
# ✅ Async process
# ==========================================================
async def process(user_input: str):
    async with Client("http://127.0.0.1:8000/mcp") as mcp_client:
        tools = await mcp_client.list_tools()
        openai_tools = []

        for t in tools:
            name = getattr(t, "name", "unknown_tool")
            desc = getattr(t, "description", "")
            if callable(desc):
                desc = desc()

            param_schema = getattr(t, "schema", None) or getattr(t, "input_schema", None)
            param_schema = ensure_json_object(param_schema)
            param_schema = make_json_safe(param_schema)

            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc or "No description provided.",
                    "parameters": param_schema,  # ✅ Always an object, never string
                }
            })

        # 🧠 Main chat call
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.messages,
            tools=openai_tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # 🧩 Handle tool calls
        if hasattr(message, "tool_calls") and message.tool_calls:
            for call in message.tool_calls:
                tool_name = call.function.name
                try:
                    args = json.loads(call.function.arguments)
                except Exception:
                    args = {}

                # Validate before adding registration
                if tool_name == "add_registration":
                    valid, msg = validate_inputs(args)
                    if not valid:
                        with st.chat_message("assistant"):
                            st.error(f"❌ Validation failed: {msg}")
                        st.session_state.messages.append(
                            {"role": "assistant", "content": f"❌ Validation failed: {msg}"}
                        )
                        return

                with st.spinner(f"🛠 Running `{tool_name}`..."):
                    result = await mcp_client.call_tool(tool_name, arguments=args)

                # 🧾 Handle table display
                if tool_name == "view_all_registration":
                    try:
                        data = result
                        if hasattr(result, "content"):
                            text = "".join(getattr(c, "text", "") for c in result.content)
                            data = text
                        if isinstance(data, str):
                            data = json.loads(data)
                        if isinstance(data, list) and all(isinstance(r, dict) for r in data):
                            df = pd.DataFrame(data)
                            st.session_state.table_data = df
                            st.session_state.show_table = True
                            with st.chat_message("assistant"):
                                st.success("✅ Here are all registrations:")
                                st.dataframe(df)
                            st.session_state.messages.append(
                                {"role": "assistant", "content": "✅ Displayed all registrations in table format."}
                            )
                        else:
                            with st.chat_message("assistant"):
                                st.warning("⚠️ No valid registration data found.")
                    except Exception:
                        with st.chat_message("assistant"):
                            st.error("⚠️ Unable to display registration data.")
                else:
                    with st.chat_message("assistant"):
                        st.success("✅ Registration added successfully!")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": "✅ Registration added successfully!"}
                    )

        # 💬 Handle normal assistant reply
        else:
            reply = message.content or ""
            if isinstance(reply, list):
                reply = "".join(block.get("text", "") for block in reply if isinstance(block, dict))
            if "name" in reply.lower() and "email" in reply.lower():
                reply += "\n\n🗓️ **(Please enter date in format: YYYY-MM-DD)**"
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)

# ==========================================================
# ✅ Run on user input
# ==========================================================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    asyncio.run(process(user_input))
