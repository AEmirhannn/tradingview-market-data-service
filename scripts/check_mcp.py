#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DEFAULT_REQUESTS = [
    {
        "symbol": "BINANCE:BTCUSDT",
        "interval": "1d",
        "limit": 1,
    }
]


async def _run_smoke(args):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tradingview_service.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            tool_names = sorted(tool.name for tool in tools_response.tools)

            missing_tools = sorted(
                {
                    "tv_health",
                    "tv_history",
                    "tv_history_summary",
                    "tv_history_multi",
                }
                - set(tool_names)
            )
            if missing_tools:
                raise RuntimeError(f"missing MCP tools: {', '.join(missing_tools)}")

            health = await session.call_tool("tv_health", {})
            history = await session.call_tool(
                "tv_history_multi",
                {
                    "requests": [
                        {
                            "symbol": args.symbol,
                            "interval": args.interval,
                            "limit": args.limit,
                        }
                    ]
                },
            )

            print(
                json.dumps(
                    {
                        "tools": tool_names,
                        "tv_health": _content_payload(health),
                        "tv_history_multi": _content_payload(history),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )


def _content_payload(response):
    content = getattr(response, "content", [])
    if not content:
        return None
    first = content[0]
    text = getattr(first, "text", None)
    if text is None:
        return first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def main():
    parser = argparse.ArgumentParser(description="Smoke-test the TradingView MarketData MCP server.")
    parser.add_argument("--symbol", default=DEFAULT_REQUESTS[0]["symbol"])
    parser.add_argument("--interval", default=DEFAULT_REQUESTS[0]["interval"])
    parser.add_argument("--limit", type=int, default=DEFAULT_REQUESTS[0]["limit"])
    args = parser.parse_args()

    asyncio.run(_run_smoke(args))


if __name__ == "__main__":
    main()
