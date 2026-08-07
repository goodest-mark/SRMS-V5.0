from PySide6.QtWidgets import QApplication

import ranking as ranking_module
import ui.pages.historical_results_page as historical_results_module


def test_ranking_page_stores_history_level(monkeypatch):
    app = QApplication.instance() or QApplication([])

    monkeypatch.setattr(ranking_module, "compute_student_scores", lambda *args, **kwargs: [])

    page = ranking_module.RankingPage()
    page.set_history_context(7, "Form I", level="A_LEVEL")

    assert page.history_level == "A_LEVEL"


def test_workflow_tabs_apply_checked_highlight(monkeypatch):
    app = QApplication.instance() or QApplication([])

    monkeypatch.setattr(historical_results_module.combo_loaders, "load_years", lambda *args, **kwargs: None)
    monkeypatch.setattr(historical_results_module.combo_loaders, "load_terms", lambda *args, **kwargs: None)
    monkeypatch.setattr(historical_results_module.combo_loaders, "load_all_exams_for_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(historical_results_module, "get_classes", lambda: [])

    page = historical_results_module.HistoricalResultsPage()
    page._switch_page(1)

    assert page.btn_remarks.isChecked()
    assert "QPushButton#workflowTab:checked" in page.btn_remarks.styleSheet()
