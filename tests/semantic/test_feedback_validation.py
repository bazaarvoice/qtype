"""Tests for semantic validation of feedback configurations."""

from __future__ import annotations

from qtype.semantic import loader


class TestFeedbackSemanticValidation:
    """Test semantic validation rules for feedback."""

    def test_thumbs_feedback_loads_correctly(self, tmp_path):
        """Test that thumbs feedback configuration loads and validates."""
        yaml_content = """
id: test_app
flows:
  - id: test_flow
    feedback:
      type: thumbs
      explanation: true
    steps:
      - type: Echo
        id: echo1
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        app, _ = loader.load(str(yaml_file))
        flow = app.flows[0]
        assert flow.feedback is not None
        assert flow.feedback.type == "thumbs"
        assert flow.feedback.explanation is True

    def test_rating_feedback_loads_correctly(self, tmp_path):
        """Test that rating feedback configuration loads and validates."""
        yaml_content = """
id: test_app
flows:
  - id: test_flow
    feedback:
      type: rating
      scale: 10
      explanation: false
    steps:
      - type: Echo
        id: echo1
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        app, _ = loader.load(str(yaml_file))
        flow = app.flows[0]
        assert flow.feedback is not None
        assert flow.feedback.type == "rating"
        assert flow.feedback.scale == 10
        assert flow.feedback.explanation is False

    def test_category_feedback_loads_correctly(self, tmp_path):
        """Test that category feedback configuration loads and validates."""
        yaml_content = """
id: test_app
flows:
  - id: test_flow
    feedback:
      type: category
      categories:
        - accurate
        - helpful
        - creative
      allow_multiple: true
      explanation: true
    steps:
      - type: Echo
        id: echo1
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        app, _ = loader.load(str(yaml_file))
        flow = app.flows[0]
        assert flow.feedback is not None
        assert flow.feedback.type == "category"
        assert flow.feedback.categories == ["accurate", "helpful", "creative"]
        assert flow.feedback.allow_multiple is True
        assert flow.feedback.explanation is True

    def test_flow_without_feedback(self, tmp_path):
        """Test that flows work without feedback configuration."""
        yaml_content = """
id: test_app
flows:
  - id: test_flow
    steps:
      - type: Echo
        id: echo1
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        app, _ = loader.load(str(yaml_file))
        flow = app.flows[0]
        assert flow.feedback is None
