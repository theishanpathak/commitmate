from commitmate.message_gen import clean_response

def test_clean_response_strips_markdown_fence():
    """clean_response should remove ``` fences wrapping the response."""
    raw = '```\n{"type": "feat"}\n```'
    result = clean_response(raw)
    assert result == '{"type": "feat"}'

def test_clean_response_no_fence_is_noop():
    """clean_response should return already-clean input unchanged (aside from stripping whitespace)."""
    raw = '  {"type": "feat"}        \n'
    result = clean_response(raw)
    assert result == '{"type": "feat"}'

def test_clean_response_strips_fence_with_language_tag():
    """clean_response should strip an opening fence even when it has a language tag, e.g. ```json"""
    raw = '```json\n{"type": "feat"}\n``` '
    result = clean_response(raw)
    assert result == '{"type": "feat"}'

