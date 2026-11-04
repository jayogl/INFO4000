import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ollama

# Update with the path to your server's main.py
SERVER_PATH = "weather_server.py"
MODEL_NAME = "qwen3:4b"


async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=[SERVER_PATH],
        env=None,
    )

    print("Connecting to MCP Weather Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Fetch tools exposed by your MCP server
            tool_list = await session.list_tools()
            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": getattr(
                            tool, "input_schema", getattr(tool, "inputSchema", {})
                        ),
                    },
                }
                for tool in tool_list.tools
]

            print(
                f"Connected! Available tools: {[t.name for t in tool_list.tools]}"
            )
            print(f"Running model: {MODEL_NAME}")
            print("-" * 50)

            # System prompt ensures Qwen infers coordinates and calls tools
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an assistant with access to weather tools. "
                        "When the user asks about the weather for a city or region, "
                        "use your geographic knowledge to estimate the latitude and longitude, "
                        "then invoke the appropriate weather tool. Always use the returned tool data."
                    ),
                }
            ]

            while True:
                user_input = input("\nYou: ").strip()
                if not user_input or user_input.lower() in ("exit", "quit"):
                    break

                messages.append({"role": "user", "content": user_input})

                # Step 1: Query Qwen with tools enabled
                response = ollama.chat(
                    model=MODEL_NAME, messages=messages, tools=ollama_tools
                )

                # Optional: display thinking block if Qwen3 thought through the problem
                if (
                    hasattr(response.message, "thinking")
                    and response.message.thinking
                ):
                    print(f"\n[Thinking]: {response.message.thinking.strip()}")

                # Step 2: Handle tool calls if emitted
                if response.message.tool_calls:
                    messages.append(response.message)

                    for call in response.message.tool_calls:
                        fn_name = call.function.name
                        fn_args = call.function.arguments

                        print(f"-> [MCP Tool Call] {fn_name}({fn_args})")

                        # Execute the tool via MCP
                        result = await session.call_tool(
                            name=fn_name, arguments=fn_args
                        )
                        result_text = "\n".join(
                            c.text for c in result.content if hasattr(c, "text")
                        )

                        messages.append({
                            "role": "tool",
                            "name": fn_name,
                            "content": result_text,
                        })

                    # Step 3: Let Qwen generate the final conversational response
                    final_response = ollama.chat(
                        model=MODEL_NAME, messages=messages
                    )
                    messages.append(final_response.message)
                    print(f"\nQwen: {final_response.message.content}")
                else:
                    messages.append(response.message)
                    print(f"\nQwen: {response.message.content}")


if __name__ == "__main__":
    asyncio.run(main())