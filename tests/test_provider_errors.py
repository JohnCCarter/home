"""ProviderApiError is the provider-neutral base the tools layer maps.

GraphApiError must stay a subclass so existing Microsoft paths are unchanged, and
the mapping must work for any ProviderApiError (so a future Google provider can
raise its own ProviderApiError and flow through the same tools error handling).
"""

from app.providers.base import ProviderApiError
from app.providers.outlook_provider import GraphApiError
from app.tools.contracts import map_graph_error, map_read_email_graph_error


def test_graph_error_is_a_provider_error():
    assert issubclass(GraphApiError, ProviderApiError)
    err = GraphApiError(404, "not found")
    assert isinstance(err, ProviderApiError)
    assert err.status_code == 404
    assert err.message == "not found"


def test_mapping_is_provider_neutral():
    # A plain (non-Graph) ProviderApiError maps the same way.
    assert map_graph_error(ProviderApiError(401, "auth")).code == "auth_required"
    assert map_graph_error(ProviderApiError(403, "denied")).code == "permission_denied"
    assert map_graph_error(ProviderApiError(429, "slow")).code == "rate_limited"
    assert map_graph_error(ProviderApiError(503, "down")).code == "provider_error"


def test_read_email_mapping_is_provider_neutral():
    assert map_read_email_graph_error(ProviderApiError(400, "bad id")).code == "not_found"
    assert map_read_email_graph_error(ProviderApiError(404, "missing")).code == "not_found"
