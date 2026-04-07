import json
import base64
import hmac
import hashlib
import logging
from secrets import token_bytes
from Crypto.Cipher import AES
from rest_framework.renderers import BaseRenderer
from .crypto import _get_keys, CryptoException


logger = logging.getLogger(__name__)


class AESRenderer(BaseRenderer):
    """
    Renderer personalizado que cifra TODA respuesta con AES-256-CBC + HMAC.
    
    El cliente siempre recibe:
    {
        "ciphertext": "base64(iv + ciphertext + hmac)",
        "status": 200
    }
    """
    media_type = "application/json"
    format = "json"

    def render(self, data, media_type=None, renderer_context=None):
        """
        Cifra la respuesta con AES-256-CBC + HMAC-SHA256.
        """
        try:
            aes_key, hmac_key = _get_keys()
            
            # Serializar respuesta
            plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
            
            # Generar nonce aleatorio
            nonce = token_bytes(16)
            
            # Cifrar con GCM (sin padding)
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext)
            
            # Calcular HMAC
            hmac_obj = hmac.new(hmac_key, nonce + ciphertext + tag, hashlib.sha256)
            auth_tag = hmac_obj.digest()
            
            # Empaquetar: nonce + ciphertext + tag + auth_tag
            payload = nonce + ciphertext + tag + auth_tag
            ciphertext_b64 = base64.urlsafe_b64encode(payload).decode('utf-8')
            
            # Retornar respuesta cifrada
            response = {
                "ciphertext": ciphertext_b64,
                "status": renderer_context.get('response').status_code if renderer_context else 200
            }
            
            return json.dumps(response)
            
        except CryptoException as e:
            logger.error(f"Error de cifrado en AESRenderer: {str(e)}")
            # En caso de error, retornar error sin cifrar (o cifrado si es posible)
            error_response = {"error": "Error en servidor", "detail": str(e)}
            return json.dumps(error_response)
        except Exception as e:
            logger.error(f"Error inesperado en AESRenderer: {str(e)}")
            error_response = {"error": "Error interno del servidor"}
            return json.dumps(error_response)