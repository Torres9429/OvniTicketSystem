import base64
import json
import hmac
import hashlib
from secrets import token_bytes
from Crypto.Cipher import AES
from django.conf import settings


class CryptoException(Exception):
    """Excepción base para errores de cifrado."""
    pass


class IntegrityError(CryptoException):
    """El HMAC no coincide - posible tampering."""
    pass


def _get_keys():
    """
    Obtiene las claves de cifrado desde Django settings.
    Las claves deben ser Base64-encoded en variables de entorno.
    
    Raises:
        CryptoException: Si las claves no están configuradas correctamente.
    """
    try:
        aes_key_b64 = getattr(settings, 'AES_SECRET_KEY', None)
        hmac_key_b64 = getattr(settings, 'HMAC_SECRET_KEY', None)
        
        if not aes_key_b64 or not hmac_key_b64:
            raise CryptoException(
                "AES_SECRET_KEY y HMAC_SECRET_KEY deben estar en settings.py. "
                "Ejecutar: python generate_keys.py"
            )
        
        # Decodificar de Base64
        aes_key = base64.urlsafe_b64decode(aes_key_b64)
        hmac_key = base64.urlsafe_b64decode(hmac_key_b64)
        
        # Validar longitud correcta para AES-256
        if len(aes_key) != 32:
            raise CryptoException(f"AES_SECRET_KEY debe ser 32 bytes (256 bits), se obtuvieron {len(aes_key)}")
        
        if len(hmac_key) != 32:
            raise CryptoException(f"HMAC_SECRET_KEY debe ser 32 bytes (256 bits), se obtuvieron {len(hmac_key)}")
        
        return aes_key, hmac_key
    except Exception as e:
        if isinstance(e, CryptoException):
            raise
        raise CryptoException(f"Error cargando claves de cifrado: {str(e)}")


def encrypt_payload(data: dict) -> str:
    """
    Cifra un diccionario usando AES-256-GCM con nonce aleatorio y HMAC.
    
    Args:
        data: Diccionario a cifrar
        
    Returns:
        String en formato: base64(nonce + ciphertext + tag + hmac)
        
    Raises:
        CryptoException: Si hay error en el cifrado
    """
    try:
        aes_key, hmac_key = _get_keys()
        
        # 1. Serializar y codificar datos
        plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
        
        # 2. Generar nonce aleatorio (16 bytes)
        nonce = token_bytes(16)
        
        # 3. Cifrar con AES-256-GCM (evita padding oracle de CBC)
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        
        # 4. Calcular HMAC sobre (nonce + ciphertext + tag) para autenticar
        hmac_obj = hmac.new(hmac_key, nonce + ciphertext + tag, hashlib.sha256)
        auth_tag = hmac_obj.digest()
        
        # 5. Retornar: base64(nonce + ciphertext + tag + hmac)
        payload = nonce + ciphertext + tag + auth_tag
        return base64.urlsafe_b64encode(payload).decode('utf-8')
        
    except CryptoException:
        raise
    except Exception as e:
        raise CryptoException(f"Error cifrando payload: {str(e)}")


def decrypt_payload(encrypted_data: str) -> dict:
    """
    Descifra un payload cifrado con AES-256-GCM.
    Verifica integridad con HMAC antes de descifrar.
    
    Args:
        encrypted_data: String en formato base64(nonce + ciphertext + tag + hmac)
        
    Returns:
        Diccionario descifrado
        
    Raises:
        CryptoException: Si hay error en descifrado
        IntegrityError: Si el HMAC no coincide (tampering detectado)
    """
    try:
        aes_key, hmac_key = _get_keys()
        
        # 1. Decodificar Base64
        payload = base64.urlsafe_b64decode(encrypted_data)
        
        # 2. Extraer componentes: nonce (16) + ciphertext + tag GCM (16) + hmac (32)
        nonce = payload[:16]
        auth_tag = payload[-32:]  # HMAC-SHA256 = 32 bytes
        gcm_tag = payload[-48:-32]  # Tag GCM por defecto = 16 bytes
        ciphertext = payload[16:-48]

        if len(ciphertext) == 0:
            raise CryptoException("Payload cifrado incompleto")
        
        # 3. Verificar HMAC (prevenir tampering)
        hmac_obj = hmac.new(hmac_key, nonce + ciphertext + gcm_tag, hashlib.sha256)
        expected_tag = hmac_obj.digest()
        
        if not hmac.compare_digest(auth_tag, expected_tag):
            raise IntegrityError("HMAC inválido - el payload puede haber sido modificado")
        
        # 4. Descifrar y verificar autenticidad con AES-256-GCM
        cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, gcm_tag)
        
        # 5. Deserializar JSON
        return json.loads(plaintext.decode('utf-8'))
        
    except CryptoException:
        raise
    except ValueError as e:
        raise CryptoException(f"Datos cifrados inválidos o corruptos: {str(e)}")
    except Exception as e:
        raise CryptoException(f"Error descifrando payload: {str(e)}")