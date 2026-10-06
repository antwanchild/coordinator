import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

import schedule


@contextmanager
def temporary_workbook_template():
    """Use an isolated minimal AM/PM template for workbook and route tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = Path(tmpdir) / "template.xlsx"
        workbook = Workbook()
        active_sheet = workbook.active
        assert active_sheet is not None
        active_sheet.title = "AM"
        workbook.create_sheet("PM")
        workbook.save(template_path)
        workbook.close()

        with patch.object(schedule, "TEMPLATE_PATH", str(template_path)):
            yield
