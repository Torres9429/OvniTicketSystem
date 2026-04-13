"""
Script para generar claves de cifrado seguras para AES-256 y HMAC.
Ejecutar: python generate_keys.py
Copiar el output al archivo .env
"""
import os
import base64
from secrets import token_bytes


def generate_encryption_keys():
    """
    Genera un par de claves criptográficas seguras:
    - AES_SECRET_KEY: 32 bytes (256 bits) para AES-256
    - HMAC_SECRET_KEY: 32 bytes (256 bits) para HMAC-SHA256
    """
    aes_key = token_bytes(32)
    aes_key_b64 = base64.urlsafe_b64encode(aes_key).decode('utf-8')
    
    hmac_key = token_bytes(32)
    hmac_key_b64 = base64.urlsafe_b64encode(hmac_key).decode('utf-8')
    
    print("=" * 70)
    print("CLAVES DE CIFRADO GENERADAS - Copiar al archivo .env")
    print("=" * 70)
    print("\n# Cifrado AES-256-CBC")
    print(f"AES_SECRET_KEY={aes_key_b64}")
    print("\n# Validación de integridad (HMAC-SHA256)")
    print(f"HMAC_SECRET_KEY={hmac_key_b64}")
    print("\n" + "=" * 70)
    print("⚠️  IMPORTANTE:")
    print("  1. Nunca commitear estas claves al repositorio")
    print("  2. Usar variables de entorno en producción")
    print("  3. Rotar las claves periódicamente")
    print("  4. Guardar en un gestor de secretos (AWS Secrets, HashiCorp Vault, etc)")
    print("=" * 70 + "\n")
    
    return aes_key_b64, hmac_key_b64


if __name__ == "__main__":
    aes_key, hmac_key = generate_encryption_keys()
