"""Guard: the MCP error-code Literal must stay in sync with the tools contract.

result_models.ToolErrorModel.code mirrors ToolErrorCode inline (the MCP layer must
not import app.tools.contracts, which pulls in a provider). Nothing enforced that
mirror before — a new code added to one and not the other would pass every other
test while the MCP output schema silently diverged. This test fails loudly instead.
"""

from typing import get_args

from app.mcp.result_models import ToolErrorModel
from app.tools.contracts import ToolErrorCode


def test_mcp_error_codes_match_tools_contract():
    contract_codes = set(get_args(ToolErrorCode))
    mcp_codes = set(get_args(ToolErrorModel.model_fields["code"].annotation))
    assert mcp_codes == contract_codes
