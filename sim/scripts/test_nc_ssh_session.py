"""SSH completion contract: missing status is different from a remote failure."""
from types import SimpleNamespace
import unittest

from nc_ssh_session import execute


class Channel:
    def __init__(self, code):
        self.code, self.closed = code, False

    def recv_ready(self):
        return False

    recv_stderr_ready = recv_ready

    def exit_status_ready(self):
        return True

    def recv_exit_status(self):
        return self.code

    def close(self):
        self.closed = True


class CompletionTests(unittest.TestCase):
    def test_disconnect_has_no_confirmed_remote_status(self):
        for code in (-1, 0, 9, 124):
            with self.subTest(code=code):
                channel = Channel(code)
                client = SimpleNamespace(exec_command=lambda *a, **k: (
                    SimpleNamespace(close=lambda: None), SimpleNamespace(channel=channel), None))
                result = execute(client, {"command": "remote-test"})
                self.assertEqual(result["exit_code"], code)
                self.assertEqual(result["completion_confirmed"], code >= 0)
                self.assertTrue(channel.closed)

    def test_invalid_requests_do_not_open_a_channel(self):
        for request in ({"command": ""}, {"command": "x", "timeout_s": 0},
                        {"command": "x", "timeout_s": 181}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                execute(None, request)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompletionTests))
    if result.wasSuccessful():
        print("PASS: SSH missing status remains unconfirmed; remote nonzero remains a failure")
    raise SystemExit(not result.wasSuccessful())
