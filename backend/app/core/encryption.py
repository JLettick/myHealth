"""
Encryption utilities for secure token storage.

Uses Fernet symmetric encryption to encrypt OAuth tokens before storing
them in the database.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.

    Uses Fernet symmetric encryption which provides:
    - AES-128-CBC encryption
    - HMAC-SHA256 authentication
    - Timestamp validation
    """

    def __init__(self):
        """Initialize encryption service with key from settings."""
        settings = get_settings()
        self._key = settings.encryption_key

        if not self._key:
            logger.warning("No encryption key configured - token encryption disabled")
            self._fernet = None
        else:
            try:
                self._fernet = Fernet(self._key.encode())
            except Exception as e:
                logger.error(f"Invalid encryption key format: {e}")
                self._fernet = None

    @property
    def is_configured(self) -> bool:
        """Check if encryption is properly configured."""
        return self._fernet is not None

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            ValueError: If encryption is not configured
        """
        if not self._fernet:
            raise ValueError("Encryption key not configured")

        encrypted = self._fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If encryption is not configured or decryption fails
        """
        if not self._fernet:
            raise ValueError("Encryption key not configured")

        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Failed to decrypt token - invalid or corrupted")
            raise ValueError("Failed to decrypt: invalid token")


# Singleton instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """
    Get the encryption service singleton.

    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    This should be run once to generate a key for your .env file:
        python -c "from app.core.encryption import generate_encryption_key; print(generate_encryption_key())"

    Returns:
        Base64-encoded Fernet key
    """
    return Fernet.generate_key().decode()
