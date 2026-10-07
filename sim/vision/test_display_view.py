"""Four-view staging/atomic protocol and CLI, without pretending to test hardware."""
import contextlib
import io
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/pynq_host"))
from vision_regs import VisionRegs
from test_vision_regs import Mock
import display_view


def main():
    mock = Mock()
    regs = VisionRegs(0, {"read": mock.read, "write": mock.write})
    mock.mem[0] = 0x80000006
    for view, expected in (("gray", 0x16), ("gauss", 0x17), ("edge", 0x1F), ("color", 0x0F)):
        assert regs.set_display_view(view) == 0x80000000 | expected
        assert regs.get_display_view() == view.upper()
        previous = mock.active[:]
        config = regs.commit(wait=False)
        assert mock.active == previous
        mock.frame()
        regs.wait_applied(config)
        assert mock.active[0] == mock.mem[0]
    before = mock.mem[:]
    try:
        regs.set_display_view("wrong")
        raise AssertionError("invalid view accepted")
    except ValueError:
        assert mock.mem == before
    # CLI should wait for acknowledgement, preserve independent bits and not reload.
    original_commit = regs.commit
    def acknowledge(**kwargs):
        config = original_commit(wait=False)
        mock.frame()
        regs.wait_applied(config, timeout=kwargs["timeout"])
        return config
    with patch.object(display_view, "VisionRegs", return_value=regs), patch.object(regs, "commit", side_effect=acknowledge):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            assert display_view.main(["--view", "gray"]) == 0
        assert "PASS: display=GRAY" in output.getvalue()
    mock.mem[11] = 1
    with patch.object(display_view, "VisionRegs", return_value=regs), contextlib.redirect_stdout(io.StringIO()) as output:
        assert display_view.main(["--view", "edge"]) == 1
    assert "busy" in output.getvalue()
    with contextlib.redirect_stderr(io.StringIO()):
        for argv in (["--view", "wrong"], ["--view", "gray", "--timeout", "0"]):
            try:
                display_view.main(argv)
                raise AssertionError("CLI accepted invalid input")
            except SystemExit as error:
                assert error.code == 2
    print("PASS: four display views, retained bits, frame acknowledgement, busy/error CLI mock")


if __name__ == "__main__":
    main()
