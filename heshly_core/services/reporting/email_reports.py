from __future__ import annotations

import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from heshly_core.models.reporting import ReportResult


class EmailReports:
    """
    Email Report Delivery Service

    Supports sending generated reports as
    email attachments.

    SMTP configuration should be supplied by the
    application configuration or environment variables.
    """

    def __init__(
        self,
        smtp_server: str = "localhost",
        smtp_port: int = 25,
        username: str = "",
        password: str = "",
        use_tls: bool = False,
        sender: str = "reports@heshly.com",
    ):

        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender = sender

    # =====================================================
    # Build Email
    # =====================================================

    def build_email(
        self,
        recipient: str,
        report: ReportResult,
        attachment: str | Path | None = None,
        subject: str | None = None,
        body: str | None = None,
    ) -> EmailMessage:

        message = EmailMessage()

        message["From"] = self.sender
        message["To"] = recipient

        message["Subject"] = (
            subject
            or f"Report: {report.report_id}"
        )

        message.set_content(

            body
            or (
                f"""
Hello,

Your requested report has been generated.

Report ID : {report.report_id}
Generated : {report.generated_at}
Rows      : {report.rows}

Regards,
Heshly Reporting Engine
"""
            ).strip()
        )

        if attachment:

            self._attach_file(
                message,
                Path(attachment),
            )

        return message

    # =====================================================
    # Send Email
    # =====================================================

    def send(
        self,
        recipient: str,
        report: ReportResult,
        attachment: str | Path | None = None,
        subject: str | None = None,
        body: str | None = None,
    ) -> bool:

        message = self.build_email(
            recipient=recipient,
            report=report,
            attachment=attachment,
            subject=subject,
            body=body,
        )

        try:

            with smtplib.SMTP(
                self.smtp_server,
                self.smtp_port,
            ) as smtp:

                if self.use_tls:
                    smtp.starttls()

                if self.username:

                    smtp.login(
                        self.username,
                        self.password,
                    )

                smtp.send_message(
                    message
                )

            return True

        except Exception as exc:

            print(
                f"Email send failed: {exc}"
            )

            return False

    # =====================================================
    # Batch Send
    # =====================================================

    def send_bulk(
        self,
        recipients: list[str],
        report: ReportResult,
        attachment: str | Path | None = None,
        subject: str | None = None,
        body: str | None = None,
    ) -> dict:

        results = {}

        for recipient in recipients:

            results[recipient] = self.send(

                recipient=recipient,

                report=report,

                attachment=attachment,

                subject=subject,

                body=body,

            )

        return results

    # =====================================================
    # Attachment Helper
    # =====================================================

    def _attach_file(
        self,
        message: EmailMessage,
        path: Path,
    ):

        if not path.exists():
            return

        mime_type, _ = mimetypes.guess_type(
            path
        )

        if mime_type:

            maintype, subtype = (
                mime_type.split(
                    "/",
                    1,
                )
            )

        else:

            maintype = "application"
            subtype = "octet-stream"

        with open(
            path,
            "rb",
        ) as file:

            message.add_attachment(

                file.read(),

                maintype=maintype,

                subtype=subtype,

                filename=path.name,

            )

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "smtp_server": self.smtp_server,

            "smtp_port": self.smtp_port,

            "tls_enabled": self.use_tls,

        }