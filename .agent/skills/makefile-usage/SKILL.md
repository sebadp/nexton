---
name: Makefile Command Usage
description: Reference for commonly used Makefile commands in Nexton. ALWAYS prefer these over raw docker/poetry commands.
---

# Makefile Command Usage

**CRITICAL:** You must ALWAYS use `make` commands when providing instructions to the user or executing commands yourself, unless a specific `make` command does not exist.

## 🚀 Common Commands

| Action | Make Command | Raw Command (Avoid) |
| :--- | :--- | :--- |
| **Start Services** | `make up` | `docker-compose up -d` |
| **Stop Services** | `make down` | `docker-compose down` |
| **View Logs** | `make logs` | `docker-compose logs -f app` |
| **Build Images** | `make build` | `docker-compose build` |
| **Run Tests** | `make test` | `pytest ...` |
| **Format Code** | `make format` | `black ...` |

## 💡 Lite Mode (Resource Efficient)

| Action | Make Command |
| :--- | :--- |
| **Start Lite** | `make start-lite` |
| **Start Lite w/ Logs** | `make start-lite-logs` |
| **Rebuild & Restart** | `make rebuild-lite` |
| **Rebuild Backend Only** | `make rebuild-lite-backend` |
| **Rebuild Frontend Only** | `make rebuild-lite-frontend` |

## 🛠️ Development & Database

| Action | Make Command |
| :--- | :--- |
| **Setup Project** | `make setup` |
| **Database Shell** | `make db-shell` |
| **Run Migrations** | `make migrate` |
| **Create Migration** | `make migrate-create MESSAGE="description"` |

## ⚠️ Notes

1. **If a make command exists, USE IT.**
2. If a complex command is needed repeatedly, **suggest adding it to the Makefile**.
3. Use `make help` to see all available commands.
