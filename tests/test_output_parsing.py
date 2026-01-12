from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput, parse_output


def test_parse_tool_call() -> None:
    raw = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 1, "b": 2},
    ).model_dump_json()
    parsed = parse_output(raw)
    assert isinstance(parsed, ToolCallOutput)
    assert parsed.tool_name == "math.add"


def test_parse_final() -> None:
    raw = FinalOutput(type="final", content="ok").model_dump_json()
    parsed = parse_output(raw)
    assert isinstance(parsed, FinalOutput)
    assert parsed.content == "ok"


def test_invalid_json_fallbacks_to_final() -> None:
    parsed = parse_output("not json")
    assert isinstance(parsed, FinalOutput)
    assert parsed.content == "not json"
