# Library System (LPNU)

Інформаційна система самообслуговування бібліотеки.

## 🔧 Технології
- Node.js + Express
- MySQL (mysql2)
- Python Tkinter (клієнт)
- Arduino (апаратний модуль)

## 🚀 Запуск проекту

### 1. Запуск MySQL
(через Docker або MySQL Workbench)
## 🗄️ Ініціалізація бази даних

Виконати SQL-скрипт:

```bash
mysql -u root -p < database.sql

### 2. Backend

cd backend

npm install

node server.js

### 3. Перевірка API
http://localhost:5001/api/health

### 4. Запуск клієнта
python app.py


## 📊 API приклади
- GET /api/books
- POST /api/login
- POST /api/reservations

## 👤 Тестові акаунти
reader@library.local / 1234  
admin@library.local / admin
