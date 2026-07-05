"""Unit tests for watermark module."""
from unittest.mock import MagicMock, call
from watermark import draw_watermark


class TestDrawWatermark:
    def _make_mock_canvas(self):
        canvas = MagicMock()
        return canvas

    def test_saves_and_restores_state(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc)
        canvas.saveState.assert_called_once()
        canvas.restoreState.assert_called_once()

    def test_sets_font_for_watermark(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc)
        canvas.setFont.assert_any_call('Helvetica-Bold', 60)

    def test_sets_low_opacity(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc)
        canvas.setFillAlpha.assert_called_once_with(0.1)

    def test_draws_default_watermark_text(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc)
        canvas.drawCentredString.assert_any_call(0, 0, "CONFIDENTIAL")

    def test_draws_custom_watermark_text(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc, watermark_text="DRAFT")
        canvas.drawCentredString.assert_any_call(0, 0, "DRAFT")

    def test_draws_footer_with_school_name_and_year(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc, school_name="Test School", year="2025")
        canvas.drawCentredString.assert_any_call(0, -100, "SRMS V5.0 | Test School 2025")

    def test_rotates_canvas(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc)
        canvas.rotate.assert_called_once_with(45)

    def test_translates_canvas(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc)
        canvas.translate.assert_called_once_with(300, 400)

    def test_sets_footer_font(self):
        canvas = self._make_mock_canvas()
        doc = MagicMock()
        draw_watermark(canvas, doc)
        canvas.setFont.assert_any_call('Helvetica', 8)
