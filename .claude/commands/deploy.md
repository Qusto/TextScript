---
name: deploy
description: Управление production сервером - deployment, security audit, health checks и rollback
---

# Production Deployment Command

Команда для безопасного управления production сервером Finance Coach Bot через специализированного субагента.

## 📋 Использование

```bash
/deploy <operation>
```

**Доступные операции:**

### 1. `production` - Полный deployment на production
Выполняет полный цикл deployment с backup, проверками и validation.

```bash
/deploy production
```

**Что происходит:**
- 🔍 Pre-deployment checks (disk, docker, database, .env)
- 💾 Database backup (сохраняется 3 последних)
- 📥 Git pull latest code
- 🔨 Docker containers rebuild
- ⏳ Waiting for services startup (30s)
- 🧪 Post-deployment validation (health checks)
- 📊 Detailed report

**Требует подтверждения:** ✅ Да (на каждом критическом шаге)

---

### 2. `audit` - Security audit (read-only)
Проверяет безопасность production сервера без изменений.

```bash
/deploy audit
```

**Что проверяется:**
- 🔒 Exposed ports (должны быть только 80, 443, 22)
- 🛡️ Firewall status (UFW rules)
- 🔑 SSH configuration (root login, password auth)
- 📁 .env file permissions (должны быть 600)
- 🐳 Docker container security
- 📦 Available system updates
- 💾 Disk space usage
- 🔍 Recent login history

**Требует подтверждения:** ❌ Нет (read-only)

---

### 3. `health` - Health checks (read-only)
Проверяет работоспособность всех сервисов.

```bash
/deploy health
```

**Что проверяется:**
- 🐳 Docker containers status (3 expected)
- 🌐 API health endpoint (https://goal.mindtools.ru)
- 💾 Database connectivity
- 📱 Telegram webhook status
- 📊 System resources (memory, disk, load)
- 🔍 Container logs (errors in last 50 lines)
- 🔐 SSL certificate validity

**Требует подтверждения:** ❌ Нет (read-only)

---

### 4. `rollback` - Откат к предыдущей версии
Откатывает production к предыдущему состоянию.

```bash
/deploy rollback
```

**Что происходит:**
- ⏸️ Останов текущих containers
- ⏮️ Git revert к предыдущему commit
- 🔨 Rebuild containers
- 🧪 Validation health checks
- 💾 Опционально: restore database backup

**Требует подтверждения:** ✅ Да (критическая операция!)

---

## 🎯 Примеры использования

**Сценарий 1: Обычный deployment**
```bash
# Пользователь
/deploy production

# Агент
🚀 Starting production deployment...
🔍 Running pre-deployment checks...
✅ All checks passed

💾 Creating database backup...
✅ Backup created: /backups/db_20251004_183546.sql

📥 Pulling latest code...
Commits to deploy:
  abc1234 feat: Add new feature
  def5678 fix: Fix bug

⚠️ Deploy these 2 commits to production? [yes/no]

# Пользователь подтверждает
yes

# Агент продолжает...
[выполняет deployment]
✅ Deployment completed successfully!
```

**Сценарий 2: Проверка здоровья системы**
```bash
/deploy health

🏥 Health Check Report
━━━━━━━━━━━━━━━━━━━━━
Status: ✅ HEALTHY

🐳 Containers: 3/3 running
🌐 API: ✅ 200 OK (234ms)
🌍 Domain: ✅ https://goal.mindtools.ru (178ms)
💾 Database: ✅ Connected
📱 Telegram: ✅ Webhook active

📊 System Resources:
- Memory: 28% used
- Disk: 19.8% used (30.8GB free)
- Load: 0.01 (low)

✅ No issues detected
```

**Сценарий 3: Security audit**
```bash
/deploy audit

🔒 Security Audit Report
━━━━━━━━━━━━━━━━━━━━━
✅ Passed: 8 checks
⚠️ Warnings: 2

Details:
✅ Firewall: Active with correct rules
✅ SSH: Root login disabled
✅ SSH: Password auth disabled
✅ Ports: Only 80, 443, 22 exposed
✅ .env: Correct permissions (600)
✅ Docker: No privileged containers
⚠️ System updates: 18 updates available
⚠️ Disk space: 19.8% used (still safe)

📊 Recommendations:
1. Apply security updates: apt upgrade
2. Monitor disk usage trend
```

**Сценарий 4: Emergency rollback**
```bash
/deploy rollback

🔄 Rollback production to previous version?
⚠️ This will revert all recent changes!
[yes/no]

# Пользователь
yes

# Агент
🔄 Initiating rollback...
⏸️ Stopping current containers...
⏮️ Reverting to commit: abc1234
🔨 Rebuilding containers...
🧪 Running validation...
✅ Rollback completed successfully!

Current state:
- Code: abc1234 (previous working version)
- Health: ✅ HEALTHY
- Database: unchanged
```

---

## ⚠️ Важные замечания

### Безопасность
- **Backup автоматический**: База данных всегда создаётся backup перед deployment
- **Подтверждения обязательны**: Все destructive операции требуют явного "yes"
- **Read-only по умолчанию**: Audit и health не изменяют систему
- **Rollback доступен**: Можно откатиться к предыдущей версии в любой момент

### Retention Policy
- Хранится **3 последних backup** базы данных
- Старые backup удаляются автоматически
- Путь к backup: `/backups/db_YYYYMMDD_HHMMSS.sql`

### Мониторинг
- После deployment рекомендуется **мониторить логи 5-10 минут**
- Проверить критические user flows
- Убедиться что Telegram bot отвечает

### При ошибках
1. Агент **автоматически предложит rollback** если validation failed
2. Все операции логируются с timestamp
3. Backup всегда доступен для manual restore

---

## 🔧 Технические детали

**SSH Connection:**
- Host: `ubuntu-server` (из ~/.ssh/config)
- Authentication: Key-based
- User: `prospero@r929385` (видно из скриншота)

**Production Server:**
- OS: Ubuntu 24.04.3 LTS
- Project path: `~/Projects/lovable-future-calculator`
- Docker Compose: `docker-compose.production.yml`
- Containers: frontend (nginx), backend (Express), postgres (PostgreSQL 15)

**Production URL:**
- Domain: https://goal.mindtools.ru
- Health endpoint: https://goal.mindtools.ru/api/health
- Admin panel: https://goal.mindtools.ru/admin
- Telegram webhook: https://goal.mindtools.ru/api/telegram/webhook

**Helper Scripts** (на production сервере):
- `.claude/scripts/pre-deploy-check.sh` - Pre-deployment checks
- `.claude/scripts/backup-database.sh` - Database backup
- `.claude/scripts/health-check.sh` - Post-deployment validation

---

## 🎓 Best Practices

1. **Перед deployment:**
   - Запустить `/deploy health` чтобы убедиться что система здорова
   - Проверить что нет активных пользователей (опционально)
   - Убедиться что есть свежий backup (автоматически)

2. **Во время deployment:**
   - Читать все output от агента
   - Подтверждать каждый критический шаг осознанно
   - Не прерывать процесс (дождаться завершения)

3. **После deployment:**
   - Проверить health checks: `/deploy health`
   - Протестировать калькулятор на https://goal.mindtools.ru
   - Проверить Telegram bot отправкой тестового сообщения
   - Мониторить логи: `docker logs calculator-backend -f`

4. **При проблемах:**
   - Немедленно запустить `/deploy rollback`
   - Сообщить об ошибке в агента для анализа
   - Проверить backup доступность

---

## 📚 См. также

- `DEPLOYMENT.md` - Полное руководство по deployment
- `CLAUDE.md` - Архитектура проекта
- `.claude/agents/production-deployment.md` - Документация субагента
