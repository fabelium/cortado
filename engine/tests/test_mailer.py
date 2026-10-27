"""E-mail sending tests with a mocked SMTP (no real network or credentials).

Run: python3 tests/test_mailer.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import smtplib

from coffee.delivery import email_sender
from coffee.delivery.email_sender import EmailSender, MAX_ATTACHMENT_BYTES
from coffee.domain.errors import MailError

_sender = EmailSender()


class _FakeSMTP:
    """Captures the message instead of actually sending it."""

    sent = []

    def __init__(self, host, port, timeout=0):
        self.host, self.port = host, port

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        pass

    def login(self, user, password):
        self.user = user

    def send_message(self, msg):
        _FakeSMTP.sent.append(msg)


def _make_mp3(size=1000):
    path = Path(tempfile.mkdtemp()) / "clip.mp3"
    path.write_bytes(b"\x00" * size)
    return path


def test_sends_with_attachment():
    import os
    os.environ["COFFEE_SMTP_USER"] = "me@gmail.com"
    os.environ["COFFEE_SMTP_PASS"] = "app-pass"
    os.environ.pop("COFFEE_MAIL_TO", None)
    smtplib.SMTP = _FakeSMTP
    _FakeSMTP.sent.clear()

    path = _make_mp3()
    to = _sender.send_file(path, "subject", "body")
    assert to == "me@gmail.com"                       # no recipient -> to yourself
    msg = _FakeSMTP.sent[-1]
    assert msg["Subject"] == "subject"
    attachments = [p for p in msg.iter_attachments()]
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "clip.mp3"
    assert attachments[0].get_content_type() == "audio/mpeg"


def test_explicit_recipient():
    import os
    os.environ["COFFEE_SMTP_USER"] = "me@gmail.com"
    os.environ["COFFEE_SMTP_PASS"] = "app-pass"
    smtplib.SMTP = _FakeSMTP
    to = _sender.send_file(_make_mp3(), "s", "b", to_addr="other@domain.com")
    assert to == "other@domain.com"


def test_missing_credentials():
    import os
    os.environ.pop("COFFEE_SMTP_USER", None)
    os.environ.pop("COFFEE_SMTP_PASS", None)
    try:
        _sender.send_file(_make_mp3(), "s", "b")
    except MailError as error:
        assert "credentials" in str(error).lower()
    else:
        raise AssertionError("should fail without credentials")


def test_oversize_attachment():
    import os
    os.environ["COFFEE_SMTP_USER"] = "me@gmail.com"
    os.environ["COFFEE_SMTP_PASS"] = "app-pass"
    big = _make_mp3(MAX_ATTACHMENT_BYTES + 1)
    try:
        _sender.send_file(big, "s", "b")
    except MailError as error:
        assert "limit" in str(error).lower() or "over" in str(error).lower()
    else:
        raise AssertionError("should reject oversize attachments")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
