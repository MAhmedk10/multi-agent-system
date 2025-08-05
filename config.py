import os,requests
import chainlit as cl
from datetime import datetime
from agents import Agent,Runner,function_tool,OpenAIChatCompletionsModel,AsyncOpenAI,RunConfig
from dataclasses import dataclass
from openai.types.responses import ResponseTextDeltaEvent

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=client
)

run_config = RunConfig(
    model,
    client,
    tracing_disabled=True
)



