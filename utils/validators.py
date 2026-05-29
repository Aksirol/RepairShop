import re

def validate_phone(phone: str) -> bool:
    """
    Перевіряє телефон на відповідність базовому українському формату.
    """
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    # Змінено: додали ? після \+, щоб плюс також був необов'язковим
    pattern = re.compile(r"^(?:\+?38)?(0\d{9})$")
    return bool(pattern.match(cleaned))

def validate_email(email: str) -> bool:
    if not email:
        return True
    pattern = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    return bool(pattern.match(email))