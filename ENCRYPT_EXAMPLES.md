"""
EJEMPLO: Cómo usar cifrado en tus vistas Django

Copiar estos patrones a tus views.py
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.common.crypto import encrypt_payload, decrypt_payload, CryptoException, IntegrityError
from apps.common.renders import AESRenderer


# ============================================================================
# EJEMPLO 1: GET - Retornar datos cifrados
# ============================================================================

class ProductoListAPIView(APIView):
    """
    GET /api/productos/
    Retorna lista de productos cifrada
    """
    renderer_classes = [AESRenderer]  # ← Cifra la respuesta automáticamente
    
    def get(self, request):
        # Lógica normal de la app
        productos = [
            {"id": 1, "nombre": "iPhone", "precio": 999},
            {"id": 2, "nombre": "Samsung", "precio": 799},
        ]
        
        # AESRenderer cifra esto automáticamente
        return Response(productos, status=status.HTTP_200_OK)


# ============================================================================
# EJEMPLO 2: POST - Recibir y procesar datos cifrados
# ============================================================================

class ProductoCreateAPIView(APIView):
    """
    POST /api/productos/
    Cliente envía: {"ciphertext": "base64..."}
    """
    renderer_classes = [AESRenderer]
    
    def post(self, request):
        # Obtener ciphertext
        ciphertext = request.data.get("ciphertext")
        
        if not ciphertext:
            return Response(
                {"error": "Field 'ciphertext' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # DESCIFRAR los datos del cliente
            payload = decrypt_payload(ciphertext)
            
        except IntegrityError:
            # HMAC falló - posible tampering
            return Response(
                {"error": "Payload integrity check failed"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        except CryptoException as e:
            # Error en descifrado
            return Response(
                {"error": f"Failed to decrypt payload: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar campos requeridos
        required_fields = ["nombre", "precio"]
        missing = [f for f in required_fields if f not in payload]
        
        if missing:
            return Response(
                {"error": f"Missing required fields: {missing}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Procesar datos (aquí iría tu lógica de negocio)
        # Por ejemplo: Crear producto en DB
        # producto = Producto.objects.create(**payload)
        
        # RESPUESTA CIFRADA (AESRenderer se encarga)
        return Response(
            {
                "message": "Producto creado exitosamente",
                "producto": payload
            },
            status=status.HTTP_201_CREATED
        )


# ============================================================================
# EJEMPLO 3: PUT - Actualizar con datos cifrados
# ============================================================================

class ProductoUpdateAPIView(APIView):
    """
    PUT /api/productos/<id>/
    Actualiza producto con datos cifrados
    """
    renderer_classes = [AESRenderer]
    
    def put(self, request, pk):
        try:
            # producto = Producto.objects.get(pk=pk)
            pass  # Tu lógica
        except Exception:
            return Response(
                {"error": "Producto not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        ciphertext = request.data.get("ciphertext")
        
        if not ciphertext:
            return Response(
                {"error": "Field 'ciphertext' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payload = decrypt_payload(ciphertext)
        except IntegrityError:
            return Response(
                {"error": "Payload was tampered with"},
                status=status.HTTP_403_FORBIDDEN
            )
        except CryptoException as e:
            return Response(
                {"error": f"Decryption failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar producto
        # producto.nombre = payload.get("nombre", producto.nombre)
        # producto.precio = payload.get("precio", producto.precio)
        # producto.save()
        
        return Response(
            {"message": "Producto actualizado", "updated": payload},
            status=status.HTTP_200_OK
        )


# ============================================================================
# EJEMPLO 4: DELETE - Con validación de integridad
# ============================================================================

class ProductoDeleteAPIView(APIView):
    """
    DELETE /api/productos/<id>/
    Elimina producto
    """
    renderer_classes = [AESRenderer]
    
    def delete(self, request, pk):
        try:
            # producto = Producto.objects.get(pk=pk)
            # producto.delete()
            pass  # Tu lógica
        except Exception:
            return Response(
                {"error": "Producto not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {"message": f"Producto {pk} eliminado"},
            status=status.HTTP_200_OK
        )


# ============================================================================
# EJEMPLO 5: Patrón Reutilizable - Mixin Helper
# ============================================================================

class EncryptedPayloadMixin:
    """
    Mixin para automatizar el descifrado de payloads
    Uso: class MyView(EncryptedPayloadMixin, APIView): ...
    """
    renderer_classes = [AESRenderer]
    
    def decrypt_request_payload(self, request):
        """
        Descifra y valida el payload del cliente.
        Retorna (datos, error_response) o (None, None) si error
        """
        ciphertext = request.data.get("ciphertext")
        
        if not ciphertext:
            error = Response(
                {"error": "Field 'ciphertext' required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            return None, error
        
        try:
            return decrypt_payload(ciphertext), None
            
        except IntegrityError:
            error = Response(
                {"error": "Tampering detected"},
                status=status.HTTP_403_FORBIDDEN
            )
            return None, error
            
        except CryptoException as e:
            error = Response(
                {"error": f"Decryption error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            return None, error


# Uso del Mixin:
class ProductoListView(EncryptedPayloadMixin, APIView):
    def post(self, request):
        payload, error = self.decrypt_request_payload(request)
        
        if error:
            return error
        
        # payload ya está descifrado y validado
        # Tu lógica aquí...
        
        return Response({"ok": True})


# ============================================================================
# EJEMPLO 6: Cifrar datos MANUALMENTE (sin AESRenderer)
# ============================================================================

def some_business_logic_function():
    """
    Ejemplo: Cifrar datos sensibles antes de guardarlos en BD
    """
    sensitive_data = {
        "ssn": "123-45-6789",
        "credit_card": "4532-XXXX-XXXX-1234"
    }
    
    # Cifrar
    encrypted = encrypt_payload(sensitive_data)
    
    # Guardar en BD (como string)
    # usuario.encrypted_ssn = encrypted
    # usuario.save()
    
    # Más tarde...
    # encrypted_from_db = usuario.encrypted_ssn
    # original_data = decrypt_payload(encrypted_from_db)


# ============================================================================
# EJEMPLO 7: Manejo de Errores en Producción
# ============================================================================

import logging

logger = logging.getLogger(__name__)


class RobustAPIView(APIView):
    """
    Ejemplo de manejo de errores robusto para producción
    """
    renderer_classes = [AESRenderer]
    
    def post(self, request):
        try:
            ciphertext = request.data.get("ciphertext")
            
            if not ciphertext:
                return Response(
                    {"error": "Invalid request"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                payload = decrypt_payload(ciphertext)
            except IntegrityError as e:
                logger.warning(f"Tampering attempt detected: {request.META.get('REMOTE_ADDR')}")
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
            except CryptoException as e:
                logger.error(f"Crypto error: {e}")
                return Response(
                    {"error": "Server error"},  # No revelar detalles
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Procesar...
            return Response({"ok": True})
            
        except Exception as e:
            logger.exception("Unexpected error in POST")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# CLIENTE JAVASCRIPT - Ejemplo descifrado en frontend
# ============================================================================

"""
// En frontend (JavaScript)

async function encryptPayload(data) {
  const key = await getAESKey();  // Desde config
  const plaintext = JSON.stringify(data);
  
  const iv = crypto.getRandomValues(new Uint8Array(16));
  const ciphertext = await crypto.subtle.encrypt(
    {name: "AES-CBC", iv},
    key,
    new TextEncoder().encode(plaintext)
  );
  
  return btoa([...iv, ...new Uint8Array(ciphertext)].join(','));
}

async function decryptPayload(ciphertext_b64) {
  const key = await getAESKey();
  const payload = Uint8Array.from(
    atob(ciphertext_b64).split(',').map(x => parseInt(x))
  );
  
  const iv = payload.slice(0, 16);
  const encrypted = payload.slice(16);
  
  const plaintext = await crypto.subtle.decrypt(
    {name: "AES-CBC", iv},
    key,
    encrypted
  );
  
  return JSON.parse(new TextDecoder().decode(plaintext));
}

// Uso:
const data = {usuario: 'john', email: 'john@example.com'};
const encrypted = await encryptPayload(data);

const response = await fetch('/api/productos/', {
  method: 'POST',
  body: JSON.stringify({ciphertext: encrypted}),
  headers: {'Content-Type': 'application/json'}
});

const responseData = await response.json();
const decrypted = await decryptPayload(responseData.ciphertext);
console.log(decrypted);  // Original data
"""
