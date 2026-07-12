import re

COMMON_PASSWORDS = {
    "123456", "12345678", "123456789", "password", "contraseña",
    "admin", "admin123", "administrador", "letmein", "welcome",
    "qwerty", "abc123", "monkey", "master", "dragon",
    "login", "prueba", "test", "test123", "empresa",
    "1234567890", "1234567", "password1", "passw0rd",
    "iloveyou", "sunshine", "trustno1", "football", "baseball",
}

MIN_LENGTH = 8
MIN_UPPER = 1
MIN_LOWER = 1
MIN_DIGIT = 1
MIN_SPECIAL = 1
SPECIAL_CHARS = r"[!@#$%^&*(),.?\":{}|<>_\-\\\/\[\]'`~]"


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < MIN_LENGTH:
        return False, f"Debe tener al menos {MIN_LENGTH} caracteres"

    if password.lower() in COMMON_PASSWORDS:
        return False, "Esta contraseña es demasiado común"

    if sum(1 for c in password if c.isupper()) < MIN_UPPER:
        return False, f"Debe contener al menos {MIN_UPPER} mayúscula"

    if sum(1 for c in password if c.islower()) < MIN_LOWER:
        return False, f"Debe contener al menos {MIN_LOWER} minúscula"

    if sum(1 for c in password if c.isdigit()) < MIN_DIGIT:
        return False, f"Debe contener al menos {MIN_DIGIT} dígito"

    if len(re.findall(SPECIAL_CHARS, password)) < MIN_SPECIAL:
        return False, f"Debe contener al menos {MIN_SPECIAL} carácter especial (!@#$%^&*)"

    return True, ""
