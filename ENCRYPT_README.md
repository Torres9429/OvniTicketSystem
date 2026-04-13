# Cifrado de Payloads con AES-256-CBC + HMAC-SHA256

## 📋 Descripción General

Sistema robusto para cifrado/descifrado de payloads en Django usando:
- **AES-256-CBC**: Cifrado de datos
- **HMAC-SHA256**: Validación de integridad (previene tampering)
- **IV aleatorio**: Un vector de inicialización diferente para cada cifrado (seguridad criptográfica)
- **Base64**: Codificación de datos binarios para transmisión

## 🔑 Paso 1: Generar Claves de Cifrado

Las claves deben ser generadas una sola vez y guardadas en variables de entorno.

```bash
# Generar claves seguras
python generate_keys.py
```

Esto producirá output similar a:
```
======================================================================
CLAVES DE CIFRADO GENERADAS - Copiar al archivo .env
======================================================================

# Cifrado AES-256-CBC
AES_SECRET_KEY=AbC1De2Fg3Hi4Jk5Lm6No7Pq8Rs9Tu0Vw1Xy2Za3bc=

# Validación de integridad (HMAC-SHA256)
HMAC_SECRET_KEY=XyZ9Wv8Us7Tr6Qp5Om4Ln3Km2Jl1Ih0Gf9Ed8Rc7Bq=

======================================================================
```

## 📝 Paso 2: Configurar Variables de Entorno

### Crear archivo `.env` en raíz del proyecto:

```bash
# Django
SECRET_KEY=your-django-secret-here
DEBUG=True

# Cifrado (copiar del output de generate_keys.py)
AES_SECRET_KEY=AbC1De2Fg3Hi4Jk5Lm6No7Pq8Rs9Tu0Vw1Xy2Za3bc=
HMAC_SECRET_KEY=XyZ9Wv8Us7Tr6Qp5Om4Ln3Km2Jl1Ih0Gf9Ed8Rc7Bq=

# Database
DB_ENGINE=django.db.backends.mysql
DB_NAME=ovni_ticket_system
DB_USER=root
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306
```

### ⚠️ Importante:
- **NUNCA** commitar `.env` al repositorio
- Agregar `.env` al `.gitignore`
- En producción, usar gestor de secretos (AWS Secrets Manager, Vault, etc)

## 🔐 Uso en Código

### Cifrar un Payload

```python
from apps.common.crypto import encrypt_payload

data = {
    "user_id": 123,
    "username": "john_doe",
    "email": "john@example.com"
}

# Cifrar
encrypted = encrypt_payload(data)
# Retorna: "base64(iv + ciphertext + hmac)"
```

### Descifrar un Payload

```python
from apps.common.crypto import decrypt_payload, IntegrityError

encrypted = "AbC1De2Fg3Hi4Jk5..."

try:
    data = decrypt_payload(encrypted)
    print(data)  # {'user_id': 123, 'username': 'john_doe', ...}
except IntegrityError:
    print("⚠️  El payload fue modificado (tampering detectado)")
except Exception as e:
    print(f"Error descifrado: {e}")
```

## 🌐 Uso en APIs - AESRenderer

El `AESRenderer` cifra automáticamente todas las respuestas:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.renders import AESRenderer

class MyAPIView(APIView):
    renderer_classes = [AESRenderer]
    
    def get(self, request):
        data = {"message": "Hello World"}
        return Response(data)  # Se cifra automáticamente
```

### Respuesta al Cliente (Automat cifrada):

```json
{
  "ciphertext": "AbC1De2Fg3Hi4Jk5Lm6No7Pq8Rs9Tu0Vw1Xy2Za3bc==",
  "status": 200
}
```

### Cliente Descifra (JavaScript/Web Crypto API):

```javascript
async function decryptPayload(ciphertext) {
  const key = await crypto.subtle.importKey(
    'raw',
    buffer, // De variable de entorno
    'AES-CBC',
    false,
    ['decrypt']
  );
  
  const decrypted = await crypto.subtle.decrypt(
    'AES-CBC',
    key,
    encryptedData
  );
  
  return JSON.parse(new TextDecoder().decode(decrypted));
}
```

## 🧪 Ejecutar Testes

```bash
# Todos los testes de cifrado
python manage.py test apps.common.tests.test_crypto

# Con verbosidad
python manage.py test apps.common.tests.test_crypto -v 2

# Un test específico
python manage.py test apps.common.tests.test_crypto.CryptoTestCase.test_encrypt_decrypt_roundtrip
```

## 🔄 Flujo Completo: API Segura

### 1️⃣ Cliente Cifra y Envía:
```javascript
// Cliente
const data = {producto: "iPhone", precio: 999};
const encrypted = await encryptAES(data);
fetch('/api/productos/', {
  method: 'POST',
  body: JSON.stringify({ciphertext: encrypted})
});
```

### 2️⃣ Servidor Descifra:
```python
class ProductoCreateView(APIView):
    def post(self, request):
        ciphertext = request.data.get('ciphertext')
        try:
            data = decrypt_payload(ciphertext)
            # Procesar datos
            return Response({"ok": True})
        except IntegrityError:
            return Response({"error": "Tampering detectado"}, status=400)
```

### 3️⃣ Servidor Cifra Respuesta:
```python
# AESRenderer cifra automáticamente
return Response({"resultado": "éxito"})
# Cliente recibe: {"ciphertext": "...", "status": 200}
```

## ⚙️ Configuración Avanzada

### Variables de django.conf.settings:

```python
# En config/settings/settings.py

# Cargar desde .env (ya configurado)
AES_SECRET_KEY = config('AES_SECRET_KEY')
HMAC_SECRET_KEY = config('HMAC_SECRET_KEY')
```

## 🛡️ Características de Seguridad

| Característica | Beneficio |
|---|---|
| **AES-256-CBC** | Estándar militar de cifrado |
| **IV Aleatorio** | Produce ciphertext diferente cada vez (imposible predecir) |
| **HMAC-SHA256** | Verifica que datos no hayan sido modificados |
| **Base64** | Codificación segura para transportar datos binarios |
| **Validación de Integridad** | `IntegrityError` si hay tampering |

## ⚠️ Controles de Seguridad

```python
# Automáticamente verifica:
decrypt_payload(encrypted)

# 1. IV válido (16 bytes)
# 2. Ciphertext válido
# 3. HMAC coincide (IntegrityError si no) ← Previene tampering
# 4. Plaintext es JSON válido
# 5. Descomprime a diccionario
```

## 🚨 Errores Comunes

### Error: `AES_SECRET_KEY y HMAC_SECRET_KEY no están configuradas`

**Solución:**
```bash
python generate_keys.py
# Copiar output a .env
```

### Error: `HMAC inválido - el payload puede haber sido modificado`

**Causa:** El payload fue alterado en tránsito o por un tercero
**Solución:** Detectar integridad y rechazar:
```python
try:
    data = decrypt_payload(encrypted)
except IntegrityError:
    return Response({"error": "Acceso denegado"}, status=403)
```

### Error: `El plaintext descifrado no es JSON válido`

**Causa:** Corrupción de datos o tamaño incorrecto
**Solución:** Ensayar manejo de excepciones
```python
from apps.common.crypto import CryptoException

try:
    data = decrypt_payload(encrypted)
except CryptoException as e:
    logger.error(f"Cifrado error: {e}")
    return Response({"error": "Datos inválidos"}, status=400)
```

## 📊 Estructura de Datos Cifrados

```
Base64(iv + ciphertext + hmac)
       ↓
   [16 bytes] + [variable] + [32 bytes]
```

- **IV**: 16 bytes (128 bits) - Aleatorio, noSecret
- **Ciphertext**: Variable (plaintext + padding)
- **HMAC**: 32 bytes (256 bits) - SHA256

## 🔄 Rotación de Claves

Cuando necesites cambiar las claves (recomendado anualmente):

1. Generar nuevas claves: `python generate_keys.py`
2. Actualizar en variable de entorno
3. Los datos antiguos cifrados con clave anterior NO se podrán descifrar
4. Optinal: Descifrar con clave antigua → Recifrar con nueva

## 📚 Recursos

- [PyCryptodome Documentation](https://pycryptodome.readthedocs.io/)
- [NIST AES Standard](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197.pdf)
- [OWASP Crypto Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [Django Security](https://docs.djangoproject.com/en/6.0/topics/security/)
