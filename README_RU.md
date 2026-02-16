# IPTV Backend v2 (мультипользовательский) — пошаговая инструкция (Windows)

Коротко: вы (админ) создаёте пользователя и выдаёте ему **код активации**.  
Пользователь вводит код → получает токен → видит только “свои” каналы (по назначенным пакетам).

---

## 1) Установка Docker Desktop

1. Откройте браузер и найдите: **Docker Desktop download**
2. Скачайте Docker Desktop и установите.
3. Запустите Docker Desktop и дождитесь статуса **Docker is running**.

---

## 2) Распаковка проекта

1. Создайте папку: `C:\iptv-backend-v2\`
2. Распакуйте архив проекта туда.

В папке должны быть:
- `docker-compose.yml`
- `Dockerfile`
- `README_RU.md`
- папка `app\`

---

## 3) ВАЖНО: поменять секреты

Откройте `docker-compose.yml` (Блокнот/Notepad) и поменяйте:

- `ADMIN_KEY=change-me`  → на свой секрет (длинная строка)
- `TOKEN_SECRET=change-me-too` → на свой секрет

Пример:
- `ADMIN_KEY=MySecretAdminKey_123456`
- `TOKEN_SECRET=MyTokenSecret_987654`

---

## 4) Запуск сервера

1) Откройте **PowerShell** (Пуск → PowerShell)  
2) Выполните:

```powershell
cd C:\iptv-backend-v2
docker compose up -d --build
```

---

## 5) Проверка

Откройте на ПК:
- `http://localhost:8000/docs`

Если открылась страница Swagger — сервер работает.

---

## 6) Админ-настройка через /docs (пакет → плейлист → пользователь)

### 6.0) Ввод X-Admin-Key в Swagger
1) На странице `/docs` нажмите **Authorize**
2) В поле `X-Admin-Key` вставьте ваш `ADMIN_KEY`
3) Нажмите **Authorize** и **Close**

### 6.1) Создать пакет
`POST /api/admin/packages` → Try it out → Execute  
Тело:
```json
{ "name": "Базовый" }
```
Скопируйте `package_id`.

### 6.2) Прикрепить плейлист к пакету (URL или файл)
- URL: `POST /api/admin/packages/{package_id}/playlist/from_url`
- Файл: `POST /api/admin/packages/{package_id}/playlist/upload`

После Execute вернётся `playlist_id` и будет попытка загрузить EPG.

### 6.3) Создать пользователя (получить код)
`POST /api/admin/users`  
Тело:
```json
{ "note": "Иван, Базовый", "device_limit": 2 }
```
Сохраните:
- `user_id`
- `code` (код активации)

### 6.4) Назначить пользователю пакет
`POST /api/admin/users/{user_id}/packages/{package_id}` → Execute

---

## 7) Что делает пользователь (активация кода)

### 7.1) Получить access_token
`POST /api/auth/activate`  
Тело:
```json
{ "code": "ВАШ_КОД", "device_id": "phone-1" }
```

Скопируйте `access_token`.

### 7.2) Ввести Bearer token в Swagger
Нажмите **Authorize** и вставьте `access_token` в поле `Bearer token`.

Теперь доступны:
- `GET /api/me/groups`
- `GET /api/me/channels?group=Россия`
- `GET /api/me/epg/now_next/{tvg_id}`

---

## 8) Если с телефона не открывается

1) Узнайте IP ПК:
- Win+R → `cmd`
- `ipconfig`
- найдите **IPv4 Address**, например `192.168.0.50`

2) На телефоне открывайте:
- `http://192.168.0.50:8000/docs`

Если не открывается — добавьте правило Windows Firewall для TCP порта **8000**.

---

## 9) Остановить сервер
```powershell
cd C:\iptv-backend-v2
docker compose down
```

---

## 10) Где хранятся данные
Папка `data\` рядом с проектом:
- `data\db\app.db`
- `data\playlists\`
- `data\epg\`
