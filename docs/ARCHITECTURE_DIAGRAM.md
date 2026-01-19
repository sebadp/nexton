# LinkedIn AI Agent - Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Interface"
        U[User]
        B[Browser/CLI]
    end

    subgraph "Application Layer"
        API[FastAPI API<br/>:8000]
        SVC[Service Layer<br/>Business Logic]

        API --> SVC
    end

    subgraph "AI/ML Pipeline"
        DSP[DSPy Pipeline<br/>Analysis & Scoring]
        LLM[LLM Provider<br/>Ollama/OpenAI/Anthropic]

        DSP --> LLM
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Opportunities DB)]
        RD[(Redis<br/>Cache & Queue)]
    end

    subgraph "Background Jobs"
        CEL[Celery Workers<br/>Async Processing]
        BEAT[Celery Beat<br/>Scheduler]
        SCR[LinkedIn Scraper<br/>Playwright]

        BEAT --> CEL
        CEL --> SCR
    end

    subgraph "External Services"
        LI[LinkedIn<br/>Messages]
        SMTP[Email<br/>SMTP Server]
    end

    subgraph "Observability Stack"
        PROM[Prometheus<br/>Metrics :9090]
        GRAF[Grafana<br/>Dashboards :3000]
        JAEG[Jaeger<br/>Traces :16686]
        LOKI[Loki<br/>Logs]
        FLOW[Flower<br/>Celery Monitor :5555]
    end

    %% User interactions
    U --> B
    B --> API

    %% API flow
    SVC --> DSP
    SVC --> PG
    SVC --> RD

    %% Background processing
    API --> RD
    RD --> CEL
    CEL --> SVC

    %% Scraping flow
    SCR --> LI
    SCR --> SVC

    %% Notifications
    SVC --> SMTP

    %% Observability
    API -.-> PROM
    SVC -.-> PROM
    DSP -.-> JAEG
    API -.-> JAEG
    CEL -.-> LOKI
    CEL --> FLOW

    style API fill:#4CAF50
    style DSP fill:#FF9800
    style PG fill:#2196F3
    style RD fill:#F44336
    style CEL fill:#9C27B0
    style PROM fill:#E91E63
    style GRAF fill:#FF5722
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant L as LinkedIn
    participant S as Scraper
    participant C as Celery
    participant D as DSPy
    participant DB as PostgreSQL
    participant R as Redis
    participant E as Email

    Note over L,S: Step 1: Scraping (Every 15 min)
    C->>S: Trigger scrape_messages task
    S->>L: Login & fetch messages
    L-->>S: Return messages
    S->>C: Queue analysis tasks

    Note over C,DB: Step 2: Analysis
    C->>R: Check cache
    alt Cache Hit
        R-->>C: Return cached analysis
    else Cache Miss
        C->>D: Analyze message
        D->>D: Extract info, score, classify
        D-->>C: Return analysis
        C->>R: Cache result
    end
    C->>DB: Store opportunity

    Note over C,E: Step 3: Notification
    alt High Priority (A/B tier)
        C->>D: Generate response
        D-->>C: AI response
        C->>E: Send email notification
        E-->>U: Email with opportunity
    end

    Note over U,L: Step 4: Review & Send
    U->>API: Approve response
    API->>C: Queue send_message task
    C->>S: Send via Playwright
    S->>L: Post message
    L-->>S: Confirm sent
    S->>DB: Update status
```

## Component Architecture

```mermaid
graph LR
    subgraph "API Layer"
        R1[/opportunities]
        R2[/responses]
        R3[/health]
        R4[/metrics]
    end

    subgraph "Service Layer"
        OS[OpportunityService]
        RS[ResponseService]
    end

    subgraph "Repository Layer"
        OR[OpportunityRepo]
        RR[ResponseRepo]
    end

    subgraph "Domain Models"
        OM[Opportunity]
        RM[Response]
        AM[Analysis]
    end

    R1 --> OS
    R2 --> RS
    OS --> OR
    RS --> RR
    OR --> OM
    RR --> RM
    OS --> AM

    style OS fill:#4CAF50
    style RS fill:#4CAF50
    style OR fill:#2196F3
    style RR fill:#2196F3
```

## DSPy Pipeline Flow

```mermaid
graph TD
    START[LinkedIn Message] --> ANALYZE[OpportunityAnalyzer]

    ANALYZE --> EXTRACT[Extract Info<br/>company, role, salary, tech]
    EXTRACT --> SCORE[Score Opportunity<br/>tech match, salary, seniority]
    SCORE --> CLASSIFY[Classify Tier<br/>A / B / C / D]

    CLASSIFY --> CACHE{Cache Result}
    CACHE -->|60 sec TTL| STORE[Store in PostgreSQL]

    STORE --> CHECK{High Priority?}
    CHECK -->|A or B tier| GENERATE[ResponseGenerator]
    CHECK -->|C or D tier| SKIP[Skip notification]

    GENERATE --> DETECT[Detect Language<br/>Spanish / English]
    DETECT --> CONTEXT[Add Context<br/>user profile, preferences]
    CONTEXT --> LLM[LLM Generation<br/>Ollama/OpenAI/Anthropic]
    LLM --> RESPONSE[AI Response]

    RESPONSE --> NOTIFY[Send Email]
    SKIP --> END[End]
    NOTIFY --> END

    style ANALYZE fill:#FF9800
    style GENERATE fill:#FF9800
    style LLM fill:#F44336
    style NOTIFY fill:#4CAF50
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        subgraph "Core Services"
            APP[app<br/>FastAPI<br/>Port: 8000]
            WORKER[celery-worker<br/>4 workers]
            BEAT[celery-beat<br/>Scheduler]
            SCRAPER[scraper<br/>Playwright]
        end

        subgraph "Data Services"
            PG[(postgres<br/>Port: 5432)]
            REDIS[(redis<br/>Port: 6379)]
            OLLAMA[ollama<br/>Port: 11434]
        end

        subgraph "Monitoring (Optional)"
            PROM[prometheus<br/>Port: 9090]
            GRAF[grafana<br/>Port: 3000]
            JAEG[jaeger<br/>Port: 16686]
            LOKI[loki<br/>Port: 3100]
            FLOW[flower<br/>Port: 5555]
        end
    end

    APP --> PG
    APP --> REDIS
    APP --> OLLAMA
    WORKER --> PG
    WORKER --> REDIS
    WORKER --> OLLAMA
    SCRAPER --> PG
    SCRAPER --> REDIS

    APP -.-> PROM
    WORKER -.-> PROM
    PROM --> GRAF
    APP -.-> JAEG
    WORKER -.-> LOKI

    style APP fill:#4CAF50
    style WORKER fill:#9C27B0
    style PG fill:#2196F3
    style REDIS fill:#F44336
    style OLLAMA fill:#FF9800
```

## Caching Strategy

```mermaid
graph LR
    REQ[Request] --> CHECK{Check Cache}

    CHECK -->|Hit| RETURN[Return Cached]
    CHECK -->|Miss| PROCESS[Process Request]

    PROCESS --> LLM[Call LLM]
    LLM --> STORE[Store in Cache]
    STORE --> RETURN

    RETURN --> RESP[Response]

    subgraph "Cache Layers"
        L1[LLM Results<br/>TTL: 3600s]
        L2[API Responses<br/>TTL: 300s]
        L3[DB Queries<br/>TTL: 60s]
    end

    style CHECK fill:#FFC107
    style STORE fill:#4CAF50
```

## Observability Stack

```mermaid
graph TB
    subgraph "Application"
        APP[FastAPI]
        WORKER[Celery Workers]
        SCRAPER[Scraper]
    end

    subgraph "Metrics Collection"
        APP -->|/metrics| PROM[Prometheus]
        WORKER -->|metrics| PROM
        SCRAPER -->|metrics| PROM

        PROM --> GRAF[Grafana Dashboards]
    end

    subgraph "Distributed Tracing"
        APP -->|OTLP| JAEG[Jaeger]
        WORKER -->|OTLP| JAEG
    end

    subgraph "Log Aggregation"
        APP -->|JSON logs| PROM2[Promtail]
        WORKER -->|JSON logs| PROM2
        SCRAPER -->|JSON logs| PROM2

        PROM2 --> LOKI[Loki]
        LOKI --> GRAF
    end

    subgraph "Task Monitoring"
        WORKER -->|tasks| FLOW[Flower]
    end

    style PROM fill:#E91E63
    style GRAF fill:#FF5722
    style JAEG fill:#9C27B0
    style LOKI fill:#00BCD4
    style FLOW fill:#8BC34A
```

## Security Architecture

```mermaid
graph TB
    USER[User] -->|HTTPS| LB[Load Balancer]
    LB --> APP[FastAPI App]

    APP -->|Environment Vars| SECRETS[Secrets Manager]
    APP -->|Parameterized Queries| DB[(Database)]
    APP -->|Pydantic Validation| INPUT[Input Validation]

    subgraph "Security Layers"
        INPUT --> RATE[Rate Limiting]
        RATE --> AUTH[Authentication]
        AUTH --> AUTHZ[Authorization]
    end

    subgraph "Data Protection"
        DB --> ENCRYPT[Encryption at Rest]
        APP --> TLS[TLS in Transit]
    end

    subgraph "Security Scanning"
        CODE[Code] --> BANDIT[Bandit]
        CODE --> SAFETY[Safety Check]
        DOCKER[Docker Images] --> TRIVY[Trivy Scan]
    end

    style INPUT fill:#4CAF50
    style RATE fill:#FFC107
    style AUTH fill:#FF9800
    style ENCRYPT fill:#2196F3
```

---

## Technology Stack Visualization

```mermaid
mindmap
  root((LinkedIn AI Agent))
    Backend
      FastAPI
      Python 3.11+
      Pydantic
      SQLAlchemy
      Alembic
    AI/ML
      DSPy
      Ollama
      OpenAI
      Anthropic
    Data
      PostgreSQL 15
      Redis 7
      Celery 5
    Scraping
      Playwright
      Chromium
    Observability
      Prometheus
      Grafana
      Jaeger
      Loki
      OpenTelemetry
    DevOps
      Docker
      Docker Compose
      GitHub Actions
```

---

## Performance Characteristics

| Component | Latency (p95) | Throughput | Notes |
|-----------|---------------|------------|-------|
| **API (no LLM)** | < 100ms | 100+ req/s | With caching |
| **DSPy Pipeline** | 2-4s | 15 msg/min | Single worker |
| **Cache Hit** | < 10ms | 1000+ req/s | Redis lookup |
| **Database Query** | < 10ms | 500+ qps | With indexes |
| **LLM Call (Ollama)** | 1-3s | 20+ req/min | Local inference |
| **LLM Call (OpenAI)** | 0.5-2s | 60+ req/min | API limits |

---

## Scaling Strategy

```mermaid
graph LR
    subgraph "Horizontal Scaling"
        APP1[App 1] --> LB[Load Balancer]
        APP2[App 2] --> LB
        APP3[App N] --> LB

        W1[Worker 1] --> REDIS[Redis Queue]
        W2[Worker 2] --> REDIS
        W3[Worker N] --> REDIS
    end

    subgraph "Vertical Scaling"
        CPU[Add CPU Cores]
        MEM[Add Memory]
        GPU[Add GPU<br/>for LLM]
    end

    subgraph "Data Scaling"
        PG[PostgreSQL] --> REPLICA[Read Replicas]
        REDIS --> CLUSTER[Redis Cluster]
    end

    style LB fill:#4CAF50
    style REDIS fill:#F44336
    style GPU fill:#FF9800
```

---

## Next Steps

To create a more visual diagram:

1. **Using draw.io** (recommended):
   - Go to https://app.diagrams.net/
   - Import `ARCHITECTURE_DIAGRAM.md`
   - Export as PNG/SVG
   - Save to `docs/images/architecture.png`

2. **Using Excalidraw**:
   - Go to https://excalidraw.com/
   - Draw architecture manually
   - Export as PNG
   - Save to `docs/images/architecture-simple.png`

3. **Using Mermaid Live Editor**:
   - Go to https://mermaid.live/
   - Copy diagrams from above
   - Export as PNG/SVG
   - Save to `docs/images/`
