# 🚀 Quick Start - Cifrado Seguro en Django

## 1️⃣ Generar Claves (Una sola vez)

```bash
python generate_keys.py
```

Verás output como:
```
AES_SECRET_KEY=vWxYzAbCdEfGhIjKmNoP...
HMAC_SECRET_KEY=qRsTuVwXyZaBcDeFgHi...
```

## 2️⃣ Configurar .env

Copia el contenido de `generate_keys.py` output al archivo `.env`:

```bash
# En raíz del proyecto
AES_SECRET_KEY=vWxYzAbCdEfGhIjKmNoP...
HMAC_SECRET_KEY=qRsTuVwXyZaBcDeFgHi...
```

## 3️⃣ Usar en tus Views

### Opción A: Automat cifradas (Recomendado)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.renders import AESRenderer

class MyView(APIView):
    renderer_classes = [AESRenderer]  # ← Todo se cifra
    
    def get(self, request):
        return Response({"data": "secreto"})
```

### Opción B: Cifrar manualmente

```python
from apps.common.crypto import encrypt_payload, decrypt_payload

# Cifrar
encrypted = encrypt_payload({"user": "john"})

# Descifrar
data = decrypt_payload(encrypted)
```

## 4️⃣ Recibir datos cifrados desde cliente

```python
from apps.common.crypto import decrypt_payload, IntegrityError

class MyView(APIView):
    def post(self, request):
        ciphertext = request.data.get("ciphertext")
        
        try:
            data = decrypt_payload(ciphertext)
            # data está seguro, fue validado con HMAC
        except IntegrityError:
            return Response({"error": "Access denied"}, status=403)
```

## 5️⃣ Ejecutar Tests

```bash
python manage.py test apps.common.tests -v 2
```

## ⚠️ Importante

- **NO** commitear `.env` (agregar a `.gitignore`)
- Usar diferentes claves para dev/prod
- En producción, usar gestor de secretos (AWS, Vault, etc)
- Rotar claves anualmente

## 📚 Documentación Completa

- [ENCRYPT_README.md](./ENCRYPT_README.md) - Guía detallada
- [ENCRYPT_EXAMPLES.md](./ENCRYPT_EXAMPLES.md) - Ejemplos de código
- [generate_keys.py](./generate_keys.py) - Generador de claves

## 🔐 Características

✅ AES-256 (estándar militar)  
✅ IV aleatorio (diferente cada cifrado)  
✅ HMAC-SHA256 (detecta tampering)  
✅ Base64 (compatible con web)  
✅ Validación de integridad  
✅ Manejo robusto de errores  
✅ Testes incluidos  

## 🚨 Troubleshooting

### Error: "claves no están configuradas"
```bash
python generate_keys.py
# Copiar output a .env
```

### Error: "HMAC inválido"
Los datos fueron modificados. Esto es correcto - significa que funciona la validación.

### Error: "No se pudo descifrar"
Verifica que estés usando la misma clave. Las claves no son modificables.

---

**Listo!** Tu Django está seguro. Cualquier pregunta, ver [ENCRYPT_README.md](./ENCRYPT_README.md)
