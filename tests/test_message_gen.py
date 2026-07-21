import pytest

from commitmate.message_gen import clean_response, parse_model_response, assemble_commit_message
from commitmate.exceptions import InvalidModelResponseError



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



def test_parse_model_response_valid_input():
    """A well-formed JSON response should parse successfully into a dict."""
    cleaned = '{"type": "feat", "scope": "api", "description": "add new endpoint", "body": ""}'
    result = parse_model_response(cleaned)
    assert result["type"] == "feat"
    assert result["description"] == "add new endpoint"



def test_parse_model_response_invalid_type_raises():
    """A type not in COMMIT_TYPES should raise InvalidModelResponseError."""
    cleaned = '{"type": "banana", "scope": "api", "description": "add new endpoint", "body": ""}'
    with pytest.raises(InvalidModelResponseError):
        parse_model_response(cleaned)


    
def test_parse_model_response_malformed_json_raises():
    """Invalid JSON syntax should raise InvalidModelResponseError, not crash with json.JSONDecodeError."""
    cleaned = "[type, test, body]"
    with pytest.raises(InvalidModelResponseError):
        parse_model_response(cleaned)



def test_parse_model_word_count_validation():
    """Description less than three words should raise InvalidModelResponseError"""
    cleaned = '{"type": "feat", "scope": "api", "description": "add new", "body": ""}'
    with pytest.raises(InvalidModelResponseError):
        parse_model_response(cleaned)



def test_parse_model_response_coerces_list_body():
    """A body returned as a JSON array should be coerced into a newline-joined string."""
    cleaned = '{"type": "feat", "scope": "api", "description": "add new endpoint", "body": ["item one", "item two"]}'
    result = parse_model_response(cleaned)
    assert result["body"] == "item one\nitem two"



def test_assemble_commit_message_with_scope():
    """A description with a scope should format as 'type(scope): description'."""
    data = {"type": "feat", "scope": "api", "description": "add new endpoint", "body": ""}
    result = assemble_commit_message(data)
    assert result == "feat(api): add new endpoint"



def test_assemble_commit_message_without_scope():
    """A description without any scope should format as 'type: description'."""
    data = {"type": "feat", "scope": "", "description": "add new endpoint", "body": ""}
    result = assemble_commit_message(data)
    assert result == "feat: add new endpoint"




def test_assemble_commit_message_with_body():
    """A description with a body should format as 'type(scope): description\n\nbody'."""
    data = {"type": "feat", "scope": "api", "description": "add new endpoint", "body": "item one\nitem two"}
    result = assemble_commit_message(data)
    assert result == "feat(api): add new endpoint\n\nitem one\nitem two"


def test_assemble_commit_message_without_body():
    """A description without any body should format as 'type(scope): description, no trailing body."""
    data = {"type": "feat", "scope": "api", "description": "add new endpoint", "body": ""}
    result = assemble_commit_message(data)
    assert result == "feat(api): add new endpoint"

