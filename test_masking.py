import unittest
import re
import hashlib
from faker import Faker

# --- IMPORTAMOS LA LÓGICA DE TU MAIN.PY (Simulada aquí para la prueba) ---
fake = Faker('es_MX')

def mascara_hash_email(valor):
    if not valor: return None
    salt = "SECRETO_CLASE_ABD"
    return f"{hashlib.sha256((valor + salt).encode()).hexdigest()[:12]}@dom.com"

def mascara_preservar_formato(valor):
    if not valor: return None
    nums = fake.numerify(text="##########")
    return f"+52 ({nums[:3]}) {nums[3:6]}-{nums[6:]}"

def mascara_redaccion(valor):
    if not valor or len(valor) < 5: return "****"
    return "****-****-****-" + valor[-4:]

class TestEnmascaramiento(unittest.TestCase):

    # a. Entrada vacía/nula -> salida segura
    def test_entrada_nula(self):
        self.assertIsNone(mascara_hash_email(None))
        self.assertIsNone(mascara_preservar_formato(None))
        print("✅ Test Nulos: APROBADO")

    # b. Mapeo determinístico (Mismo input = Mismo output siempre)
    def test_deterministico(self):
        email_input = "ernesto@unam.mx"
        resultado1 = mascara_hash_email(email_input)
        resultado2 = mascara_hash_email(email_input)
        self.assertEqual(resultado1, resultado2)
        print(f"✅ Test Determinístico: {resultado1} == {resultado2}")

    # c. Mantener formatos (Regex)
    def test_formato_telefono(self):
        resultado = mascara_preservar_formato("Cualquier cosa")
        # Regex para: +52 (3 digitos) 3 digitos-4 digitos
        patron = r"^\+52 \(\d{3}\) \d{3}-\d{4}$"
        self.assertTrue(re.match(patron, resultado))
        print(f"✅ Test Formato: {resultado} cumple con Regex")

    # d. Sin fuga/liga (No debe contener el valor original)
    def test_sin_fuga(self):
        tarjeta_real = "1234-5678-9012-3456"
        resultado = mascara_redaccion(tarjeta_real)
        # Verificamos que los primeros digitos NO aparezcan
        self.assertNotIn("1234", resultado)
        self.assertIn("3456", resultado) # Los ultimos 4 sí deben estar
        print(f"✅ Test Sin Fuga: {tarjeta_real} -> {resultado}")

if __name__ == '__main__':
    unittest.main()