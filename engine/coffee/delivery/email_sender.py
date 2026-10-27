"""E-mail delivery adapter (SMTP).

``EmailSender`` sends the resulting MP3 as an attachment over SMTP. Credentials
are read from environment variables (never hard-coded):

    COFFEE_SMTP_USER   sender account/e-mail (e.g. you@gmail.com)
    COFFEE_SMTP_PASS   app password (Gmail: Account > Security > 2-step
                       verification > App passwords)
    COFFEE_MAIL_TO     default recipient (optional; defaults to the sender,
                       i.e. you e-mail it to yourself)
    COFFEE_SMTP_HOST   defaults to smtp.gmail.com
    COFFEE_SMTP_PORT   defaults to 587 (STARTTLS)

Gmail caps attachments at 25 MB; we reject anything above 24 MB.
"""

from __future__ import annotations

import mimetypes
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from coffee.domain.errors import MailError

MAX_ATTACHMENT_BYTES = 24 * 1024 * 1024  # margin below Gmail's 25 MB limit


class EmailSender:
    """Adapter that sends a file as an SMTP attachment."""

    @staticmethod
    def _build_message(
        sender: str, recipient: str, subject: str, body: str, attachment: Path
    ) -> EmailMessage:
        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        ctype, _ = mimetypes.guess_type(attachment.name)
        maintype, subtype = (ctype or "audio/mpeg").split("/", 1)
        message.add_attachment(
            attachment.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=attachment.name,
        )
        return message

    def send_file(
        self, path: Path, subject: str, body: str, to_addr: str | None = None
    ) -> str:
        """Send ``path`` as an SMTP attachment. Returns the final recipient.

        Raises ``MailError`` on missing credentials, oversize attachment or any
        SMTP error.
        """
        user = os.environ.get("COFFEE_SMTP_USER")
        password = os.environ.get("COFFEE_SMTP_PASS")
        if not user or not password:
            raise MailError(
                "Missing credentials: set COFFEE_SMTP_USER and COFFEE_SMTP_PASS "
                "(on Gmail, an 'app password')."
            )

        recipient = to_addr or os.environ.get("COFFEE_MAIL_TO") or user
        host = os.environ.get("COFFEE_SMTP_HOST", "smtp.gmail.com")
        port = int(os.environ.get("COFFEE_SMTP_PORT", "587"))

        if not path.exists():
            raise MailError(f"File to send does not exist: {path}")
        size = path.stat().st_size
        if size > MAX_ATTACHMENT_BYTES:
            raise MailError(
                f"The attachment is {size / (1024*1024):.1f} MB, over the "
                f"{MAX_ATTACHMENT_BYTES // (1024*1024)} MB e-mail limit. Use --limit "
                "to trim fragments or share the file by other means."
            )

        message = self._build_message(user, recipient, subject, body, path)
        try:
            with smtplib.SMTP(host, port, timeout=60) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(user, password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as error:
            raise MailError(f"Could not send the e-mail: {error}") from error
        return recipient
