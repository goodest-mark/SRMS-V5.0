from PySide6.QtWidgets import QApplication

import ranking as ranking_module


def test_ranking_page_stores_history_level(monkeypatch):
    app = QApplication.instance() or QApplication([])

    monkeypatch.setattr(ranking_module, "compute_student_scores", lambda *args, **kwargs: [])

    page = ranking_module.RankingPage()
    page.set_history_context(7, "Form I", level="A_LEVEL")

    assert page.history_level == "A_LEVEL"
