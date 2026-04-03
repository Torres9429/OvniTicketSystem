# 🔐 Sistema de Cifrado Django + Frontend

Documentación completa del sistema de cifrado con AES-256-CBC + HMAC-SHA256

## 📚 Estructura

```
OvniTicketSystem/
├── Backend (Django):
│   ├── generate_keys.py              # ⭐ Generar claves
│   ├── .env.example                  # Template .env
│   ├── ENCRYPT_QUICKSTART.md         # Quick Start Backend
│   ├── ENCRYPT_README.md             # Documentación Backend
│   ├── ENCRYPT_EXAMPLES.md           # Ejemplos Backend
│   ├── apps/common/
│   │   ├── crypto.py                 # ✨ Módulo de cifrado (MEJORADO)
│   │   ├── renders.py                # ✨ AESRenderer (MEJORADO)
│   │   └── tests.py                  # Tests de cifrado
│   └── config/settings/
│       └── settings.py               # ✨ Configuración (UPDATED)
│
└── Frontend (JS/React/Vue):
    ├── frontend-examples/
    │   ├── crypto.js                 # Cifrado en Web Crypto API
    │   ├── api-client.js             # Cliente HTTP con cifrado
    │   ├── examples.js               # Ejemplos (Usuarios, Roles)
    │   ├── test-crypto.js            # Tests automáticos
    │   ├── test-interactive.html     # ⭐ UI interactiva para probar
    │   ├── .env.example              # Template .env frontend
    │   ├── FRONTEND_QUICKSTART.md    # Quick Start Frontend
    │   └── FRONTEND_README.md        # Documentación Frontend
```

## 🚀 Inicio Rápido (Personas Impacientes)

### Backend (10 segundos)
```bash
python generate_keys.py
# Copiar output a .env
```

### Frontend (2 minutos)
1. Abre: `frontend-examples/test-interactive.html`
2. Pega las claves en la UI
3. Click "🔒 Cifrar" y "🔓 Descifrar"
4. ✅ Listo!

## 📖 Documentación por Nivel

### 👨‍💼 Para Manager/Product
- Leer: [ENCRYPT_README.md](./ENCRYPT_README.md#características-de-seguridad)
- Conocer: Seguridad, Cifrado AES-256, HMAC, IV aleatorio

### 👨‍💻 Para Desarrollador Backend
1. [ENCRYPT_QUICKSTART.md](./ENCRYPT_QUICKSTART.md)
2. [ENCRYPT_README.md](./ENCRYPT_README.md)
3. [ENCRYPT_EXAMPLES.md](./ENCRYPT_EXAMPLES.md)

### 👩‍💻 Para Desarrollador Frontend
1. [frontend-examples/FRONTEND_QUICKSTART.md](./frontend-examples/FRONTEND_QUICKSTART.md)
2. [frontend-examples/FRONTEND_README.md](./frontend-examples/FRONTEND_README.md)
3. [frontend-examples/examples.js](./frontend-examples/examples.js)

### 🧪 Para QA/Testing
- Ejecutar: [frontend-examples/test-interactive.html](./frontend-examples/test-interactive.html)
- Tests: `python manage.py test apps.common.tests -v 2`

## 🎯 Casos de Uso

### Caso 1: Proteger datos sensibles
```python
# Backend
from apps.common.crypto import encrypt_payload
encrypted = encrypt_payload(ssn_data)
```

### Caso 2: API segura end-to-end
```python
# Backend
class UserCreate(APIView):
    renderer_classes = [AESRenderer]  # Cifra respuesta
    def post(self, request):
        ciphertext = request.data.get('ciphertext')
        payload = decrypt_payload(ciphertext)  # Descifra request
```

```javascript
// Frontend
const newUser = await apiClient.post('/usuarios/', userData);
// Cifra automáticamente antes de enviar
// Descifra automáticamente la respuesta
```

### Caso 3: Flujo completo
1. **Frontend:** Usuario ingresa "Juan García"
2. **Frontend:** Se cifra con AES + HMAC
3. **HTTP:** Envía `{"ciphertext": "base64..."}`
4. **Backend:** Verifica HMAC (/integridad)
5. **Backend:** Descifra con AES
6. **Backend:** Procesa datos seguros
7. **Backend:** Cifra respuesta
8. **HTTP:** Devuelve `{"ciphertext": "base64...", "status": 200}`
9. **Frontend:** Descifra respuesta
10. **Frontend:** Muestra datos al usuario

## 🔐 Características de Seguridad

✅ **AES-256-CBC** - Estándar militar de cifrado
✅ **IV Aleatorio** - Diferente para cada cifrado (imposible predecir)
✅ **HMAC-SHA256** - Verifica integridad de datos
✅ **Validación** - Rechaza datos tamponeados/modificados
✅ **Base64** - Codificación segura para transmisión
✅ **Web Crypto API** - API nativa del navegador (sin dependencias)
✅ **PyCryptodome** - Librería confiable para Python
✅ **Error Handling** - Manejo robusto de excepciones

## ⚙️ Configuración

### Backend (.env)
```
SECRET_KEY=your-secret-here
AES_SECRET_KEY=base64...  # Generar con generate_keys.py
HMAC_SECRET_KEY=base64...
DB_ENGINE=django.db.backends.mysql
DB_NAME=ovni_ticket_system
```

### Frontend (.env)
```
REACT_APP_AES_SECRET_KEY=base64...    # MISMO que backend
REACT_APP_HMAC_SECRET_KEY=base64...   # MISMO que backend
REACT_APP_BASE_URL=http://localhost:8000/api
```

## 🧪 Testing

### Backend
```bash
python manage.py test apps.common.tests -v 2
```

### Frontend (Interactivo)
1. Abre: `frontend-examples/test-interactive.html`
2. Llena las claves
3. Click "▶️ Ejecutar Todas las Pruebas"

### Frontend (Automático)
```bash
npm test  # Si tienes Jest/Vitest configurado
```

## 📊 Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                         USUARIO                             │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (JS)                          │
│                                                             │
│  1. Usuario ingresa datos                                  │
│  2. Valida JSON                                            │
│  3. Genera IV aleatorio                                    │
│  4. Cifra con AES-256-CBC                                  │
│  5. Calcula HMAC-SHA256                                    │
│  6. Codifica Base64                                        │
│  7. Envía: {"ciphertext": "base64(iv+cipher+hmac)"}        │
└─────────────────────────────────────────────────────────────┘
                    HTTPS/TLS TRANSPORT
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Django)                         │
│                                                             │
│  1. Recibe {"ciphertext": "..."}                           │
│  2. Decodifica Base64                                      │
│  3. Extrae: IV (16B) + Ciphertext + HMAC (32B)             │
│  4. Verifica HMAC → detect tampering                       │
│  5. Descifra con AES-256-CBC                               │
│  6. Procesa datos                                          │
│  7. Genera IV aleatorio                                    │
│  8. Cifra respuesta                                        │
│  9. Calcula HMAC                                           │
│  10. Envía: {"ciphertext": "...", "status": 200}           │
└─────────────────────────────────────────────────────────────┘
                    HTTPS/TLS TRANSPORT
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (JS)                          │
│                                                             │
│  1. Recibe {"ciphertext": "..."}                           │
│  2. Decodifica Base64                                      │
│  3. Verifica HMAC                                          │
│  4. Descifra con AES-256-CBC                               │
│  5. Parsea JSON                                            │
│  6. Actualiza UI                                           │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                         USUARIO                             │
│                    (Datos protegidos)                       │
└─────────────────────────────────────────────────────────────┘
```

## 🎓 Recursos de Aprendizaje

- [PyCryptodome Docs](https://pycryptodome.readthedocs.io/)
- [Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API)
- [OWASP Crypto Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [NIST AES Standard](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197.pdf)

## ⚠️ Consideraciones Importantes

### Claves
- ✅ Generar con: `python generate_keys.py`
- ✅ Usar variables de entorno
- ✅ Diferentes claves para dev/prod
- ❌ No hardcodear
- ❌ No commitear al repositorio
- ❌ No compartir en mensajes

### HTTPS
- ✅ Usar HTTPS en producción
- ✅ Certificados válidos
- ❌ Nunca HTTP en producción
- ❌ No ignorar errores SSL

### Testing
- ✅ Ejecutar tests antes de deploy
- ✅ Verificar integridad de datos
- ✅ Probar tampering detection
- ✅ Auditar logs de errores

## 🚨 Troubleshooting

| Error | Causa | Solución |
|---|---|---|
| "Claves no configuradas" | Variables de entorno faltantes | `python generate_keys.py` y rellenar .env |
| "HMAC failed" | Datos modificados | Normal - indica tampering detectado |
| "JSON inválido" | Plaintext corrupto | Cifra o claves incorrectas |
| "Web Crypto API not available" | Navegador antiguo | Actualizar navegador |
| "HTTPS required" | En producción con HTTP | Usar HTTPS |

## 📝 Checklist Antes de Deploy

- [ ] Generar claves con `python generate_keys.py`
- [ ] Configurar `.env` en backend
- [ ] Configurar `.env` en frontend
- [ ] Ejecutar tests: `python manage.py test apps.common.tests`
- [ ] Ejecutar tests frontend: `test-interactive.html`
- [ ] Usar HTTPS en producción
- [ ] NO commitear .env
- [ ] Agregar .env a .gitignore
- [ ] Usar gestor de secretos (AWS, Vault, etc)
- [ ] Auditar logs de seguridad

## 📞 Soporte

Para preguntas:
1. **Backend:** Ver [ENCRYPT_README.md](./ENCRYPT_README.md)
2. **Frontend:** Ver [frontend-examples/FRONTEND_README.md](./frontend-examples/FRONTEND_README.md)
3. **Tests:** Ejecutar `test-interactive.html`
4. **Ejemplos:** Ver archivos EXAMPLES.md

---

**¡Listo!** Tu sistema está protegido con cifrado de grado militar. 🔐🚀
