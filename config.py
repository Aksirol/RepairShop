import os
import logging

# Шляхи проекту
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'db')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
DB_PATH = os.path.join(DB_DIR, 'repair_shop.db')

# --- АВТОМАТИЧНЕ СТВОРЕННЯ ПАПОК ---
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
# -----------------------------------

# Константи статусів замовлень
STATUS_NEW = "Новий"
STATUS_IN_PROGRESS = "В роботі"
STATUS_NEEDS_PARTS = "Потребує запчастин"
STATUS_DONE = "Готово"
STATUS_ISSUED = "Видано"

ORDER_STATUSES = [
    STATUS_NEW, STATUS_IN_PROGRESS, STATUS_NEEDS_PARTS, STATUS_DONE, STATUS_ISSUED
]

# Ролі користувачів
ROLE_ADMIN = "Адміністратор"
ROLE_MASTER = "Майстер"
ROLE_OPERATOR = "Оператор"

USER_ROLES = [ROLE_ADMIN, ROLE_MASTER, ROLE_OPERATOR]

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DOCS_DIR, "app.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)