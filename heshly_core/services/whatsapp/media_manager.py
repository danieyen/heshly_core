from __future__ import annotations

from pathlib import Path

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)


class WhatsAppMediaManager:
    """
    Central manager for WhatsApp media.

    Future responsibilities:

    • Download media
    • Upload media
    • Delete media
    • Cache media
    • Store media
    • Retrieve media
    • Validate media
    """

    def download(
        self,
        configuration: WhatsAppConfiguration,
        media_id: str,
    ) -> dict:

        #
        # Future:
        # Download media using Cloud API.
        #

        return {

            "success": True,

            "media_id": media_id,

            "operation": "download",

        }

    def upload(
        self,
        configuration: WhatsAppConfiguration,
        file_path: str,
    ) -> dict:

        #
        # Future:
        # Upload media using Cloud API.
        #

        return {

            "success": True,

            "file_path": file_path,

            "operation": "upload",

        }

    def delete(
        self,
        configuration: WhatsAppConfiguration,
        media_id: str,
    ) -> dict:

        #
        # Future:
        # Delete uploaded media.
        #

        return {

            "success": True,

            "media_id": media_id,

            "operation": "delete",

        }

    def exists(
        self,
        file_path: str,
    ) -> bool:

        return Path(
            file_path
        ).exists()

    def validate(
        self,
        file_path: str,
    ) -> bool:

        return Path(
            file_path
        ).is_file()