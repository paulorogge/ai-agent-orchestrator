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


def test_malformed_json_fallbacks_to_final() -> None:
    parsed = parse_output('{"type": "final", ')
    assert isinstance(parsed, FinalOutput)
    assert parsed.content == '{"type": "final", '


def test_tool_call_missing_tool_name_fallbacks_to_final() -> None:
    parsed = parse_output('{"type": "tool_call", "args": {"a": 1}}')
    assert isinstance(parsed, FinalOutput)


def test_tool_call_defaults_args_when_missing() -> None:
    parsed = parse_output('{"type": "tool_call", "tool_name": "math.add"}')
    assert isinstance(parsed, ToolCallOutput)
    assert parsed.args == {}


def test_tool_call_invalid_args_type_fallbacks_to_final() -> None:
    parsed = parse_output('{"type": "tool_call", "tool_name": "math.add", "args": []}')
    assert isinstance(parsed, FinalOutput)


def test_final_missing_content_fallbacks_to_final_raw() -> None:
    parsed = parse_output('{"type": "final"}')
    assert isinstance(parsed, FinalOutput)
    assert parsed.content == '{"type": "final"}'


def test_final_non_string_content_converted_to_string() -> None:
    parsed = parse_output('{"type": "final", "content": 123}')
    assert isinstance(parsed, FinalOutput)
    assert parsed.content == "123"
