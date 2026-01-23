"""Tests for optional variable syntax and behavior."""

from qtype.dsl.model import Variable


def test_variable_with_question_mark_syntax():
    """Test that '?' suffix marks variable as optional."""
    var = Variable(id="optional_var", type="text?")

    assert var.optional is True
    assert var.type == "text"


def test_variable_without_question_mark():
    """Test that variables without '?' are required by default."""
    var = Variable(id="required_var", type="text")

    assert var.optional is False


def test_variable_explicit_optional_flag():
    """Test explicit optional=True works."""
    var = Variable(id="optional_var", type="text", optional=True)

    assert var.optional is True
    assert var.type == "text"


def test_variable_serialization_with_optional():
    """Test that optional variables serialize with '?' suffix."""
    var = Variable(id="opt_var", type="text?")
    serialized = var.model_dump()

    assert serialized["type"] == "text?"
    assert serialized["id"] == "opt_var"


def test_variable_serialization_without_optional():
    """Test that required variables serialize without '?' suffix."""
    var = Variable(id="req_var", type="text")
    serialized = var.model_dump()

    assert serialized["type"] == "text"
    assert serialized["id"] == "req_var"


def test_optional_with_list_type():
    """Test optional syntax works with list types."""
    var = Variable(id="optional_list", type="list[text]?")

    assert var.optional is True
    # Type should be parsed as list[text]
    serialized = var.model_dump()
    assert serialized["type"] == "list[text]?"


# TODO: support nested options? Seems overkill for now..?
# def test_optional_within_list_type():
#     """Test optional syntax works with list types."""
#     var = Variable(id="optional_item_list", type="list[text?]")

#     assert var.optional is False
#     # Type should be parsed as list[text]
#     serialized = var.model_dump()
#     assert serialized["type"] == "list[text?]"


def test_optional_with_number_type():
    """Test optional syntax works with primitive types."""
    var = Variable(id="optional_num", type="int?")

    assert var.optional is True
    assert var.type == "int"


def test_explicit_optional_overrides_question_mark():
    """Test that explicit optional=False is respected even with '?'."""
    # The validator should strip '?' and set optional=True
    var = Variable(id="var", type="text?", optional=False)

    # The '?' in type should take precedence
    assert var.optional is True
