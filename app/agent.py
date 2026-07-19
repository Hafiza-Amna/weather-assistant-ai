# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Weather Assistant — Graph Workflow (no LLM tool calling).

Root cause of the original failure
-----------------------------------
`groq/llama-3.3-70b-versatile` sometimes generates tool calls in Llama's
native XML format  <function=get_weather{"query":"…"}</function>  instead of
the OpenAI JSON format that Groq's API requires.  Groq then rejects the
request with code: tool_use_failed regardless of temperature or tool_choice
settings at the ADK / LiteLLM layer.

Fix
----
Eliminate LLM tool calling entirely.  Use an ADK Workflow graph with three
nodes:

  START → query_parser → tool_executor → response_generator

• query_parser  (LlmAgent)     — extracts city + query_type into session state
                                  using output_key (plain JSON, no tools).
• tool_executor (FunctionNode) — reads state, calls the Python function
                                  directly, writes result back to state.
• response_generator (LlmAgent) — reads the result from state via the
                                   {tool_result} template and writes the
                                   final user-facing response.

No Groq tool-call API is involved at any point.
"""

import datetime
import json
import re
from typing import Optional
from zoneinfo import ZoneInfo

import litellm

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models.lite_llm import LiteLlm
from google.adk.workflow import START, Workflow, node

# Drop Gemini-specific params that Groq does not understand.
litellm.drop_params = True

# ---------------------------------------------------------------------------
# Groq model (no tools registered — avoids tool_use_failed entirely)
# ---------------------------------------------------------------------------
GROQ_MODEL = LiteLlm(
    model="groq/llama-3.3-70b-versatile",
    additional_drop_params=["thinking", "cached_content"],
)


# ---------------------------------------------------------------------------
# Pure-Python tool implementations (called by FunctionNode, NOT by the LLM)
# ---------------------------------------------------------------------------

def get_weather(city: str) -> str:
    """Return simulated weather for the given city."""
    q = city.lower()
    if "sf" in q or "san francisco" in q:
        return "It's 60°F (15°C) and foggy in San Francisco."
    if "faisalabad" in q:
        return "It's 104°F (40°C) and sunny with clear skies in Faisalabad."
    if "lahore" in q:
        return "It's 100°F (38°C) and partly cloudy in Lahore."
    if "karachi" in q:
        return "It's 95°F (35°C) and humid in Karachi."
    if "islamabad" in q:
        return "It's 91°F (33°C) and mostly sunny in Islamabad."
    if "new york" in q or "nyc" in q:
        return "It's 72°F (22°C) and partly cloudy in New York."
    if "london" in q:
        return "It's 59°F (15°C) and overcast with light rain in London."
    if "tokyo" in q:
        return "It's 86°F (30°C) and warm with clear skies in Tokyo."
    if "paris" in q:
        return "It's 68°F (20°C) and partly cloudy in Paris."
    if "berlin" in q:
        return "It's 64°F (18°C) and mostly cloudy in Berlin."
    if "sydney" in q:
        return "It's 61°F (16°C) and clear in Sydney."
    if "dubai" in q:
        return "It's 104°F (40°C) and sunny in Dubai."
    if "mumbai" in q or "bombay" in q:
        return "It's 88°F (31°C) and humid with partly cloudy skies in Mumbai."
    if "beijing" in q:
        return "It's 86°F (30°C) and hazy in Beijing."
    return f"It's 86°F (30°C) and sunny in {city.title()}."


def get_current_time(city: str) -> str:
    """Return the current local time for the given city."""
    # Map of city keywords to IANA timezone IDs
    CITY_TIMEZONES = [
        (("sf", "san francisco"),                                        "America/Los_Angeles"),
        (("new york", "nyc"),                                            "America/New_York"),
        (("chicago",),                                                   "America/Chicago"),
        (("los angeles", " la"),                                         "America/Los_Angeles"),
        (("london",),                                                    "Europe/London"),
        (("paris",),                                                     "Europe/Paris"),
        (("berlin",),                                                    "Europe/Berlin"),
        (("istanbul",),                                                  "Europe/Istanbul"),
        (("moscow",),                                                    "Europe/Moscow"),
        (("dubai",),                                                     "Asia/Dubai"),
        (("faisalabad", "lahore", "islamabad", "karachi", "pakistan"),   "Asia/Karachi"),
        (("mumbai", "bombay", "delhi", "india"),                         "Asia/Kolkata"),
        (("beijing", "shanghai", "china"),                               "Asia/Shanghai"),
        (("tokyo", "japan"),                                             "Asia/Tokyo"),
        (("sydney", "melbourne", "australia"),                           "Australia/Sydney"),
        (("singapore",),                                                 "Asia/Singapore"),
        (("hong kong",),                                                 "Asia/Hong_Kong"),
        (("seoul",),                                                     "Asia/Seoul"),
    ]

    q = city.lower()
    tz_id = None
    for keywords, timezone in CITY_TIMEZONES:
        if any(kw in q for kw in keywords):
            tz_id = timezone
            break

    if tz_id is None:
        supported = (
            "San Francisco, New York, Chicago, London, Paris, Berlin, Istanbul, "
            "Moscow, Dubai, Faisalabad/Pakistan, Mumbai/India, Beijing, Tokyo, "
            "Sydney, Singapore, Hong Kong, Seoul"
        )
        return (
            f"Sorry, I don't have timezone data for '{city}'. "
            f"Supported cities: {supported}."
        )

    tz = ZoneInfo(tz_id)
    now = datetime.datetime.now(tz)
    return f"The current time in {city.title()} is {now.strftime('%Y-%m-%d %H:%M:%S %Z')} ({tz_id})."


# ---------------------------------------------------------------------------
# Node 1 — Query Parser  (LlmAgent, NO tools)
# Extracts city + query_type; stores JSON in state["parsed_query"]
# ---------------------------------------------------------------------------

query_parser = LlmAgent(
    name="query_parser",
    model=GROQ_MODEL,
    instruction=(
        "Extract the city name and query type from the user's message.\n\n"
        "Reply with ONLY a single-line JSON object — no explanation, no markdown:\n"
        '  {"city": "<city name>", "query_type": "<weather|time|unknown>"}\n\n'
        "Rules:\n"
        "  • query_type must be exactly 'weather', 'time', or 'unknown'.\n"
        "  • If no city is mentioned, use 'unknown' for city too.\n\n"
        "Examples:\n"
        "  'What is the weather in Faisalabad?' "
        '→ {"city": "Faisalabad", "query_type": "weather"}\n'
        "  'What time is it in London?' "
        '→ {"city": "London", "query_type": "time"}\n'
        "  'Tell me a joke' "
        '→ {"city": "unknown", "query_type": "unknown"}\n'
    ),
    output_key="parsed_query",
)


# ---------------------------------------------------------------------------
# Node 2 — Tool Executor  (FunctionNode — no LLM call at all)
# Reads parsed_query from state, calls Python function, writes tool_result
# ---------------------------------------------------------------------------

@node
def tool_executor(ctx) -> None:
    """Call the appropriate Python tool and store the result in session state."""
    raw = ctx.state.get("parsed_query", "{}").strip()

    # Strip markdown code fences if the LLM wrapped the output
    raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

    # Parse JSON
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: try to find a JSON object anywhere in the string
        m = re.search(r'\{[^}]+\}', raw)
        parsed = json.loads(m.group()) if m else {}

    city = parsed.get("city", "unknown")
    query_type = parsed.get("query_type", "unknown")

    if query_type == "weather" and city != "unknown":
        result = get_weather(city)
    elif query_type == "time" and city != "unknown":
        result = get_current_time(city)
    elif city == "unknown" or query_type == "unknown":
        result = (
            "I'm a weather and time assistant. "
            "Please ask me about the weather or current time in a specific city."
        )
    else:
        result = f"Unknown query type '{query_type}' for city '{city}'."

    # Store for response_generator to read via template substitution
    ctx.state["tool_result"] = result


# ---------------------------------------------------------------------------
# Node 3 — Response Generator  (LlmAgent, NO tools)
# Reads tool_result via {tool_result} state template, writes final response
# ---------------------------------------------------------------------------

response_generator = LlmAgent(
    name="response_generator",
    model=GROQ_MODEL,
    instruction=(
        "You are a friendly weather and time assistant.\n\n"
        "The information has already been retrieved:\n"
        "  {tool_result}\n\n"
        "Write a clear, natural, helpful response to the user using only the "
        "information above. Do not invent any data."
    ),
)


# ---------------------------------------------------------------------------
# Workflow — three sequential nodes, zero LLM tool calls
# ---------------------------------------------------------------------------

weather_workflow = Workflow(
    name="weather_workflow",
    edges=[
        (START, query_parser),
        (query_parser, tool_executor),
        (tool_executor, response_generator),
    ],
)

# Keep root_agent alias so fast_api_app.py's `from app.agent import root_agent`
# still works.
root_agent = weather_workflow

app = App(
    root_agent=weather_workflow,
    name="app",
)
