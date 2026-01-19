# Monitoring Stack

Comprehensive observability stack for the LinkedIn Agent application using Prometheus, Grafana, Loki, and Jaeger.

## Components

### 1. **Prometheus** (Metrics)
- Collects and stores time-series metrics
- Scrapes metrics from application endpoints
- Port: `9090`
- URL: http://localhost:9090

### 2. **Grafana** (Visualization)
- Visualizes metrics, logs, and traces
- Pre-configured dashboards for LinkedIn Agent
- Port: `3000`
- URL: http://localhost:3000
- Default credentials: `admin` / `admin`

### 3. **Loki** (Logs)
- Log aggregation system
- Integrates with Grafana for log visualization
- Port: `3100`
- URL: http://localhost:3100

### 4. **Jaeger** (Tracing)
- Distributed tracing for request flows
- Traces DSPy pipeline operations
- Port: `16686` (UI)
- URL: http://localhost:16686

### 5. **Additional Exporters**
- **Redis Exporter**: Monitors Redis metrics (port `9121`)
- **Postgres Exporter**: Monitors database metrics (port `9187`)
- **Node Exporter**: System-level metrics (port `9100`)
- **cAdvisor**: Container metrics (port `8080`)

## Quick Start

### Start the Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Check service status
docker-compose -f docker-compose.monitoring.yml ps

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

### Stop the Monitoring Stack

```bash
docker-compose -f docker-compose.monitoring.yml down

# Remove volumes (WARNING: deletes all monitoring data)
docker-compose -f docker-compose.monitoring.yml down -v
```

## Accessing Services

### Grafana Dashboard
1. Navigate to http://localhost:3000
2. Login with `admin` / `admin`
3. Go to **Dashboards** → **LinkedIn Agent Dashboard**

### Prometheus
1. Navigate to http://localhost:9090
2. Use PromQL to query metrics
3. Example: `opportunities_created_total`

### Jaeger Tracing
1. Navigate to http://localhost:16686
2. Select service: `linkedin-agent`
3. View traces for request flows

## Available Metrics

### Business Metrics
- `opportunities_created_total` - Total opportunities created by tier
- `opportunities_by_tier` - Current count of opportunities by tier
- `opportunity_score_distribution` - Score distribution histogram
- `opportunity_processing_time_seconds` - Processing time

### DSPy Pipeline Metrics
- `dspy_pipeline_executions_total` - Pipeline execution count
- `dspy_pipeline_execution_time_seconds` - Pipeline latency
- `llm_api_calls_total` - LLM API call count
- `llm_api_latency_seconds` - LLM API latency
- `llm_tokens_used_total` - Token usage tracking

### Cache Metrics
- `cache_operations_total` - Cache hit/miss/error counts
- `cache_operation_latency_seconds` - Cache operation latency
- `cache_size_bytes` - Current cache size

### Database Metrics
- `db_queries_total` - Database query count
- `db_query_latency_seconds` - Query latency
- `db_connection_pool_size` - Connection pool status

## Dashboard Features

The LinkedIn Agent dashboard includes:

1. **Opportunity Creation Rate** - Track opportunity creation over time
2. **Total Opportunities Gauge** - Current total count
3. **DSPy Pipeline Latency** - P50 and P95 latency metrics
4. **Pipeline Status Distribution** - Success vs. error vs. cached
5. **Cache Hit/Miss Rate** - Cache performance
6. **Opportunities by Tier** - Distribution across tiers

## Custom Queries

### Top Companies by Score
```promql
topk(10, avg by (company) (company_average_score))
```

### Pipeline Success Rate
```promql
rate(dspy_pipeline_executions_total{status="success"}[5m])
/
rate(dspy_pipeline_executions_total[5m])
```

### Cache Hit Ratio
```promql
rate(cache_operations_total{status="hit"}[5m])
/
rate(cache_operations_total{operation="get"}[5m])
```

## Alerting

To enable alerting:

1. Configure Alertmanager in `prometheus.yml`
2. Create alert rules in `monitoring/prometheus/alerts.yml`
3. Example alerts:
   - High error rate
   - Slow pipeline execution
   - Low cache hit ratio

## Log Queries (Loki)

Access logs through Grafana:

1. Go to **Explore** in Grafana
2. Select **Loki** datasource
3. Example queries:
   ```logql
   {container="linkedin-agent-api"} |= "error"
   {container="linkedin-agent-api"} | json | level="ERROR"
   {service="worker"} |= "pipeline_execution"
   ```

## Troubleshooting

### No Data in Grafana
- Check if Prometheus is scraping: http://localhost:9090/targets
- Verify application is exposing metrics: http://localhost:8000/api/v1/metrics
- Check Grafana datasource configuration

### Jaeger No Traces
- Verify OTEL_ENABLED=true in application `.env`
- Check OTEL_EXPORTER_OTLP_ENDPOINT points to Jaeger
- Restart application after configuration changes

### High Memory Usage
- Adjust retention period in `prometheus.yml`
- Limit log retention in Loki configuration
- Scale down scrape intervals if needed

## Production Considerations

For production deployments:

1. **Persistence**: Ensure volumes are backed up
2. **Security**:
   - Change default Grafana password
   - Enable authentication on Prometheus
   - Use HTTPS/TLS
3. **Scaling**:
   - Use Prometheus federation for multiple instances
   - Deploy Loki with S3/GCS backend
   - Use Jaeger with Cassandra/Elasticsearch
4. **High Availability**:
   - Run multiple Prometheus replicas
   - Deploy Loki in microservices mode
   - Use Jaeger collector with Kafka

## Configuration Files

- `prometheus.yml` - Prometheus scrape configuration
- `loki-config.yml` - Loki configuration
- `promtail-config.yml` - Log shipping configuration
- `grafana/provisioning/` - Auto-provisioned datasources and dashboards

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
