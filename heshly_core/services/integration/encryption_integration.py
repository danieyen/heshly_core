from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EncryptionResult:
    """
    Result returned after encryption operations.
    """

    success: bool

    data: str | None = None

    message: str | None = None



class EncryptionIntegration:
    """
    High-level encryption orchestration layer.

    Connects encryption, secrets, configuration,
    masking, and sensitive data protection.
    """

    def __init__(
        self,
        encryption_service,
        secret_manager,
        secure_configuration,
        data_masking,
        sensitive_data_protection,
        audit_service,
        security_metrics,
    ):

        self.encryption_service = encryption_service

        self.secret_manager = secret_manager

        self.secure_configuration = secure_configuration

        self.data_masking = data_masking

        self.sensitive_data_protection = (
            sensitive_data_protection
        )

        self.audit_service = audit_service

        self.security_metrics = security_metrics


    # =====================================================
    # Encryption
    # =====================================================

    def encrypt(
        self,
        data: str,
    ) -> EncryptionResult:

        encrypted = self.encryption_service.encrypt(
            data
        )

        self.security_metrics.increment(
            "encryption_operations"
        )

        return EncryptionResult(

            success=True,

            data=encrypted,

            message="Data encrypted",

        )


    # =====================================================
    # Decryption
    # =====================================================

    def decrypt(
        self,
        encrypted_data: str,
    ) -> EncryptionResult:

        decrypted = self.encryption_service.decrypt(
            encrypted_data
        )

        self.security_metrics.increment(
            "decryption_operations"
        )

        return EncryptionResult(

            success=True,

            data=decrypted,

            message="Data decrypted",

        )


    # =====================================================
    # Secrets
    # =====================================================

    def get_secret(
        self,
        key: str,
    ):

        return self.secret_manager.get(
            key
        )


    def store_secret(
        self,
        key: str,
        value: str,
    ):

        return self.secret_manager.set(
            key,
            value,
        )


    # =====================================================
    # Configuration
    # =====================================================

    def get_configuration(
        self,
        key: str,
    ):

        return self.secure_configuration.get(
            key
        )


    # =====================================================
    # Data Protection
    # =====================================================

    def mask(
        self,
        data: str,
    ):

        return self.data_masking.mask(
            data
        )


    def protect_sensitive_data(
        self,
        data,
    ):

        return self.sensitive_data_protection.protect(
            data
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "encryption_integration",

            "status": "healthy",

        }