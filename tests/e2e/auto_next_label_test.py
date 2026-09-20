from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from labelme._app import MainWindow

from ..conftest import close_or_pause
from .conftest import MainWinFactory
from .conftest import click_canvas_fraction
from .conftest import draw_and_commit_polygon
from .conftest import show_window_and_wait_for_imagedata
from .conftest import submit_label_dialog


def _selected_label(win: MainWindow) -> str | None:
    items = win._docks.unique_label_list.selectedItems()
    if not items:
        return None
    return items[0].data(Qt.ItemDataRole.UserRole)


@pytest.mark.gui
def test_auto_next_label_rotates_and_annotates_points_without_popup(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = main_win(
        file_or_dir=str(data_path / "raw"),
        output_dir=str(tmp_path),
        config_overrides={
            "auto_next_label": True,
            "auto_save": False,
            "labels": ["cat", "dog", "bird"],
        },
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    canvas = win._canvas_widgets.canvas

    # A fresh session starts at the first label of the label list.
    assert _selected_label(win) == "cat"

    win._switch_canvas_mode(edit=False, create_mode="point")
    qtbot.wait(50)

    # Each click annotates the point with the selected label, no popup, and
    # then cycles the selection to the next label.
    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=(0.4, 0.4))
    qtbot.waitUntil(lambda: len(canvas.shapes) == 1, timeout=5000)
    assert canvas.shapes[0].label == "cat"
    assert canvas.shapes[0].shape_type == "point"
    assert QApplication.activeModalWidget() is None
    assert not win._label_dialog.isVisible()
    assert _selected_label(win) == "dog"

    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=(0.6, 0.6))
    qtbot.waitUntil(lambda: len(canvas.shapes) == 2, timeout=5000)
    assert canvas.shapes[1].label == "dog"
    assert _selected_label(win) == "bird"

    # Ctrl+Z removes the last point and moves the selection back to its
    # label, so the next click re-annotates it.
    qtbot.keyClick(canvas, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    qtbot.waitUntil(lambda: len(canvas.shapes) == 1, timeout=5000)
    assert canvas.shapes[0].label == "cat"
    assert _selected_label(win) == "dog"

    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=(0.6, 0.6))
    qtbot.waitUntil(lambda: len(canvas.shapes) == 2, timeout=5000)
    assert canvas.shapes[1].label == "dog"

    # A new image without annotations restarts at the first label.
    assert win._load_file(
        image_or_label_path=str(data_path / "raw" / "2011_000006.jpg")
    )
    assert _selected_label(win) == "cat"

    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=(0.5, 0.5))
    qtbot.waitUntil(lambda: len(canvas.shapes) == 1, timeout=5000)
    assert canvas.shapes[0].label == "cat"
    assert _selected_label(win) == "dog"

    # Undoing every point leaves the first label selected.
    qtbot.keyClick(canvas, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    qtbot.waitUntil(lambda: len(canvas.shapes) == 0, timeout=5000)
    assert _selected_label(win) == "cat"

    assert win._load_file(
        image_or_label_path=str(data_path / "raw" / "2011_000025.jpg")
    )
    assert _selected_label(win) == "cat"

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_auto_next_label_resumes_after_existing_annotations(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    pause: bool,
) -> None:
    win = main_win(
        file_or_dir=str(data_path / "annotated" / "2011_000003.json"),
        config_overrides={"auto_next_label": True},
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)

    # The image is annotated up to purple_diamond (the last label of its
    # list), so the round-robin wraps back to the first label.
    assert _selected_label(win) == "amber_kite"

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_auto_next_label_off_keeps_label_popup_for_points(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = main_win(
        file_or_dir=str(data_path / "raw" / "2011_000003.jpg"),
        output_dir=str(tmp_path),
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    canvas = win._canvas_widgets.canvas

    win._switch_canvas_mode(edit=False, create_mode="point")
    qtbot.wait(50)

    submit_label_dialog(qtbot=qtbot, label_dialog=win._label_dialog, label="pt")
    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=(0.5, 0.5))
    qtbot.waitUntil(lambda: len(canvas.shapes) == 1, timeout=5000)
    assert canvas.shapes[0].label == "pt"
    # Without the option no label is preselected on load either.
    assert _selected_label(win) is None

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_auto_next_label_keeps_label_popup_for_polygons(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = main_win(
        file_or_dir=str(data_path / "raw" / "2011_000003.jpg"),
        output_dir=str(tmp_path),
        config_overrides={"auto_next_label": True, "labels": ["cat", "dog"]},
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    assert _selected_label(win) == "cat"

    # Only point mode annotates without the popup; polygons still ask.
    draw_and_commit_polygon(
        qtbot=qtbot,
        win=win,
        label="poly",
        vertices=((0.6, 0.6), (0.8, 0.6), (0.8, 0.8)),
    )
    assert win._canvas_widgets.canvas.shapes[-1].label == "poly"

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)
