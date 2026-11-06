# OpsPilot Lite

**An AI-powered application monitoring and incident management platform.**

OpsPilot Lite is an AIOps platform designed to monitor application health, detect service failures, manage incidents, generate AI-powered incident analysis, and notify users about critical operational events.

The platform combines asynchronous backend processing, automated monitoring, incident lifecycle management, analytics, and AI-assisted troubleshooting.

## Key Features

### Application and Service Management
- Manage applications and their associated services.
- Track service dependencies.
- Organize and monitor application infrastructure.

### Automated Monitoring
- Configure HTTP health monitors.
- Schedule periodic health checks.
- Track monitoring results and service availability.
- Detect service failures automatically.

### Incident Management
- Automatically create incidents when monitoring failures are detected.
- Track incident lifecycle and status.
- Associate affected services with incidents.
- Maintain incident event history.
- Handle incident resolution.

### AI-Powered Incident Analysis
- Trigger asynchronous AI analysis when incidents are created.
- Generate incident analysis and persist results.
- Support AI-assisted root cause investigation and troubleshooting.

### Analytics
- Application and service health metrics.
- Incident statistics and trends.
- Mean Time To Resolution (MTTR).
- Monitoring and availability insights.

### Notification System
- Automated email notifications when incidents are created.
- Resolution notifications when incidents are resolved.
- Background notification processing.

### Asynchronous Processing
- RabbitMQ message broker.
- Celery background workers.
- Celery Beat for periodic monitoring and task scheduling.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | SQLAlchemy, configured relational database |
| Migrations | Alembic |
| Background Processing | Celery |
| Message Broker | RabbitMQ |
| HTTP Client | HTTPX |
| AI Integration | LLM-based incident analysis |
| Frontend | React, TypeScript (planned) |
| Vector Database | Qdrant (planned for RAG) |

## Architecture

OpsPilot Lite follows a layered backend architecture:

- **API Layer:** Handles HTTP requests and responses.
- **Service Layer:** Implements application business logic.
- **Repository Layer:** Handles database operations.
- **Model Layer:** Defines database entities.
- **Worker Layer:** Executes asynchronous background tasks.

### High-Level Workflow

1. Applications and services are registered.
2. Health monitors periodically check service availability.
3. Monitoring failures trigger incident creation.
4. Incident details are processed by background workers.
5. AI analysis is generated and persisted.
6. Email notifications are dispatched.
7. Analytics provide operational insights.
8. Incidents can be tracked through resolution.

## Project Structure

```text
opspilot-lite/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   │
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── frontend/
│
├── docs/
│
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- A supported relational database
- RabbitMQ
- Git

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd opspilot-lite
```

### 2. Configure the backend

```bash
cd backend

python -m venv venv
```

Activate the virtual environment.

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure the database, RabbitMQ, AI provider and email settings in `.env`.

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the FastAPI application

Use the actual ASGI application import path configured in the project.

Example:

```bash
uvicorn app.main:app --reload
```

### 5. Start Celery worker

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

### 6. Start Celery Beat

```bash
celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

Make sure RabbitMQ and the database are running before starting the application and workers.

## Environment Configuration

The application uses environment variables for configuration.

Refer to `backend/.env.example` for the required configuration fields.

**Never commit actual credentials, API keys, database passwords or SMTP credentials.**

## Roadmap

- [x] Backend architecture and database models
- [x] Repository and service layers
- [x] Application and service management
- [x] Automated monitoring
- [x] Incident lifecycle management
- [x] Dashboard analytics
- [x] Email notification processing
- [x] AI incident analysis
- [x] RabbitMQ and Celery integration
- [ ] Automated test coverage and reliability validation
- [ ] React frontend and interactive dashboard
- [ ] RAG-based historical incident retrieval
- [ ] Vector database integration
- [ ] Docker Compose deployment
- [ ] Cloud deployment and CI/CD

## Future Enhancements

- Retrieval-Augmented Generation (RAG) for historical incident analysis.
- Semantic search across previous incidents and troubleshooting documentation.
- Similar incident identification.
- Context-aware remediation recommendations.
- Interactive operational dashboard.
- Containerized deployment and automated CI/CD.

## Project Status

The core backend functionality is implemented, including monitoring, incident management, analytics, AI analysis, email notifications and asynchronous task processing.

Frontend development, RAG integration, automated testing and deployment are planned next.

---

**OpsPilot Lite — Smarter Monitoring. Faster Incident Resolution.**