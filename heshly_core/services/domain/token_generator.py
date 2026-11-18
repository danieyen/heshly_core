import secrets


class DomainTokenGenerator:

    @staticmethod
    def generate():
        return (
            "heshly-verification="
            + secrets.token_hex(16)
        )