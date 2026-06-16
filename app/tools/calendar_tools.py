from app.providers.base import ProviderApiError
from app.tools.contracts import ToolResult, map_graph_error, tool_failure, tool_success
from app.tools.deps import AuthRequiredError, get_provider_with_name
from app.tools.serialization import serialize_calendar_events


async def read_calendar() -> ToolResult:
    tool = "read_calendar"
    provider_name = "outlook"

    try:
        provider, provider_name = await get_provider_with_name()
        events = await provider.read_calendar()
        return tool_success(tool, provider_name, serialize_calendar_events(events))
    except AuthRequiredError as exc:
        return tool_failure(
            tool,
            provider_name,
            map_graph_error(ProviderApiError(401, exc.message)),
        )
    except ProviderApiError as exc:
        return tool_failure(tool, provider_name, map_graph_error(exc))
