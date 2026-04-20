"""
Testes para el módulo de cifrado crypto.py
Verifica cifrado/descifrado, validación de integridad, manejo de errores.

Para ejecutar: python manage.py test apps.common.tests.test_crypto
"""
import json
from django.test import TestCase
from apps.common.crypto import (
    encrypt_payload,
    decrypt_payload,
    CryptoException,
    IntegrityError,
)


class CryptoTestCase(TestCase):
    """Testes para cifrado y descifrado de payloads."""
    
    def setUp(self):
        """Preparar datos de prueba."""
        self.test_data = {
            "user_id": 123,
            "username": "john_doe",
            "email": "john@example.com",
            "roles": ["admin", "user"],
            "metadata": {
                "created_at": "2026-04-02T10:00:00Z",
                "ip": "127.0.0.1"
            }
        }
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test que encrypt -> decrypt preserva los datos."""
        encrypted = encrypt_payload(self.test_data)
        
        self.assertIsInstance(encrypted, str)
        self.assertTrue(len(encrypted) > 0)
        
        decrypted = decrypt_payload(encrypted)
        
        self.assertEqual(decrypted, self.test_data)
    
    def test_encrypt_produces_different_ciphertexts(self):
        """Test que cada cifrado produce ciphertext diferente (IV aleatorio)."""
        encrypted1 = encrypt_payload(self.test_data)
        encrypted2 = encrypt_payload(self.test_data)
        
        self.assertNotEqual(encrypted1, encrypted2)
        
        self.assertEqual(decrypt_payload(encrypted1), self.test_data)
        self.assertEqual(decrypt_payload(encrypted2), self.test_data)
    
    def test_decrypt_tampered_data_raises_integrity_error(self):
        """Test que descifrar datos alterados raise IntegrityError."""
        encrypted = encrypt_payload(self.test_data)
        
        encrypted_list = list(encrypted)
        encrypted_list[0] = 'X' if encrypted_list[0] != 'X' else 'Y'
        tampered = ''.join(encrypted_list)
        
        with self.assertRaises(IntegrityError):
            decrypt_payload(tampered)
    
    def test_empty_dict(self):
        """Test cifrado de diccionario vacío."""
        empty_dict = {}
        encrypted = encrypt_payload(empty_dict)
        decrypted = decrypt_payload(encrypted)
        self.assertEqual(decrypted, empty_dict)
    
    def test_unicode_data(self):
        """Test que preserva caracteres Unicode."""
        unicode_data = {
            "nombre": "José García",
            "ciudad": "São Paulo",
            "pais": "中国",
            "emoji": "🚀🔐"
        }
        encrypted = encrypt_payload(unicode_data)
        decrypted = decrypt_payload(encrypted)
        self.assertEqual(decrypted, unicode_data)
    
    def test_large_payload(self):
        """Test con payload grande."""
        large_data = {
            "items": [
                {f"field_{i}": f"value_{i}" * 100}
                for i in range(100)
            ]
        }
        encrypted = encrypt_payload(large_data)
        decrypted = decrypt_payload(encrypted)
        self.assertEqual(decrypted, large_data)
    
    def test_invalid_base64_raises_exception(self):
        """Test que Base64 inválido raises exception."""
        with self.assertRaises(CryptoException):
            decrypt_payload("not-valid-base64!!!")

    def test_decrypt_accepts_unpadded_base64url(self):
        """Acepta payloads URL-safe sin '=' padding (compatibilidad frontend)."""
        encrypted = encrypt_payload(self.test_data)
        unpadded = encrypted.rstrip("=")

        decrypted = decrypt_payload(unpadded)
        self.assertEqual(decrypted, self.test_data)
    
    def test_malformed_json_raises_exception(self):
        """Test que plaintext no-JSON raises exception."""
        encrypted = encrypt_payload(self.test_data)
        
        truncated = encrypted[:len(encrypted)-10]
        
        with self.assertRaises(CryptoException):
            decrypt_payload(truncated)
    
    def test_special_characters_in_values(self):
        """Test con caracteres especiales."""
        special_data = {
            "quotes": 'He said "Hello"',
            "backslash": "path\\to\\file",
            "newline": "line1\nline2",
            "tab": "col1\tcol2",
            "unicode_escape": "\\u0041"
        }
        encrypted = encrypt_payload(special_data)
        decrypted = decrypt_payload(encrypted)
        self.assertEqual(decrypted, special_data)
    
    def test_numeric_precision(self):
        """Test que mantiene precisión de números."""
        numeric_data = {
            "integer": 12345,
            "float": 123.456,
            "negative": -999,
            "scientific": 1.23e-4,
            "zero": 0
        }
        encrypted = encrypt_payload(numeric_data)
        decrypted = decrypt_payload(encrypted)
        
        self.assertEqual(decrypted["integer"], numeric_data["integer"])
        self.assertAlmostEqual(decrypted["float"], numeric_data["float"])
        self.assertEqual(decrypted["negative"], numeric_data["negative"])
        self.assertAlmostEqual(decrypted["scientific"], numeric_data["scientific"])
        self.assertEqual(decrypted["zero"], numeric_data["zero"])
    
    def test_boolean_values(self):
        """Test que mantiene booleanos."""
        bool_data = {
            "is_active": True,
            "is_deleted": False,
            "nullish": None
        }
        encrypted = encrypt_payload(bool_data)
        decrypted = decrypt_payload(encrypted)
        self.assertEqual(decrypted, bool_data)

    def test_payload_structure(self):
        import base64

        encrypted = encrypt_payload(self.test_data)
        raw = base64.urlsafe_b64decode(encrypted)

        iv = raw[:16]
        auth_tag = raw[-32:]
        ciphertext = raw[16:-32]

        self.assertEqual(len(iv), 16)
        self.assertEqual(len(auth_tag), 32)
        self.assertTrue(len(ciphertext) > 0)

    def test_is_valid_base64(self):
        import base64

        encrypted = encrypt_payload(self.test_data)

        try:
            base64.urlsafe_b64decode(encrypted)
        except Exception:
            self.fail("No es Base64 válido")

    def test_not_plaintext_visible(self):
        encrypted = encrypt_payload(self.test_data)

        self.assertNotIn("john_doe", encrypted)
        self.assertNotIn("john@example.com", encrypted)

    def test_hmac_integrity_manual(self):
        import base64, hmac, hashlib
        from django.conf import settings

        encrypted = encrypt_payload(self.test_data)
        raw = base64.urlsafe_b64decode(encrypted)

        iv = raw[:16]
        auth_tag = raw[-32:]
        ciphertext = raw[16:-32]

        hmac_key = base64.urlsafe_b64decode(settings.HMAC_SECRET_KEY)

        expected = hmac.new(hmac_key, iv + ciphertext, hashlib.sha256).digest()

        self.assertEqual(auth_tag, expected)



