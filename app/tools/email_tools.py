from app.providers.outlook_provider import GraphApiError
from app.tools.contracts import ToolError, ToolResult, map_graph_error, tool_failure, tool_success
from app.tools.deps import AuthRequiredError, get_provider_with_name
from app.tools.serialization import serialize_email_detail, serialize_email_messages


async def read_recent_emails() -> ToolResult:
    tool = "read_recent_emails"
    provider_name = "outlook"

    try:
        provider, provider_name = await get_provider_with_name()
        messages = await provider.read_recent_emails()
        return tool_success(tool, provider_name, serialize_email_messages(messages))
    except AuthRequiredError as exc:
        return tool_failure(
            tool,
            provider_name,
            map_graph_error(GraphApiError(401, exc.message)),
        )
    except GraphApiError as exc:
        return tool_failure(tool, provider_name, map_graph_error(exc))


async def read_email(message_id: str) -> ToolResult:
    tool = "read_email"
    provider_name = "outlook"

    if not message_id or not message_id.strip():
        return tool_failure(
            tool,
            provider_name,
            ToolError("validation_error", "message_id is required", retryable=False),
        )

    try:
        provider, provider_name = await get_provider_with_name()
        email = await provider.read_email(message_id)
        return tool_success(tool, provider_name, serialize_email_detail(email))
    except AuthRequiredError as exc:
        return tool_failure(
            tool,
            provider_name,
            map_graph_error(GraphApiError(401, exc.message)),
        )
    except GraphApiError as exc:
        return tool_failure(tool, provider_name, map_graph_error(exc))
