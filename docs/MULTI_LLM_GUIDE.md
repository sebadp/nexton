# Multi-Model LLM Support Guide

**Feature**: Sprint 3.1
**Version**: 1.2.0
**Last Updated**: January 18, 2024

---

## Overview

The LinkedIn AI Agent Platform supports **multiple LLM providers** with a unified interface:

- **OpenAI** - GPT-4, GPT-4-turbo, GPT-3.5-turbo
- **Anthropic** - Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **Ollama** - Local models (Llama2, Mistral, CodeLlama, etc.)

This allows you to:
- ✅ **Switch providers** without code changes
- ✅ **Optimize costs** by using different models for different tasks
- ✅ **Improve quality** by using the best model for each use case
- ✅ **Avoid vendor lock-in** with provider flexibility
- ✅ **Track costs** automatically per provider

---

## Quick Start

### 1. Basic Configuration

Edit your `.env` file:

```bash
# Choose your provider
LLM_PROVIDER=openai  # Options: openai, anthropic, ollama
LLM_MODEL=gpt-4

# Add API keys (only needed for cloud providers)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Restart Services

```bash
docker-compose restart api worker
```

### 3. Verify

```bash
# Check logs for LLM provider initialization
docker-compose logs api | grep -i "llm_provider\|dspy_configured"

# Expected output:
# llm_provider_created provider=openai model=gpt-4
# dspy_configured_successfully provider=openai model=gpt-4
```

---

## Provider Comparison

| Provider | Models | Cost | Speed | Quality | Best For |
|----------|--------|------|-------|---------|----------|
| **OpenAI** | GPT-4, GPT-3.5 | $$ | Fast | Excellent | General purpose, complex reasoning |
| **Anthropic** | Claude 3 | $-$$$ | Fast | Excellent | Long context, analysis, safety |
| **Ollama** | Llama2, Mistral | FREE | Medium | Good | Development, cost-sensitive, privacy |

### Detailed Comparison

#### OpenAI GPT Models

| Model | Cost (per 1K tokens) | Speed | Best For |
|-------|---------------------|-------|----------|
| **GPT-4** | $0.03 / $0.06 | Medium | Complex analysis, high quality |
| **GPT-4-turbo** | $0.01 / $0.03 | Fast | Balanced cost/quality |
| **GPT-3.5-turbo** | $0.0005 / $0.0015 | Very Fast | High volume, simple tasks |

#### Anthropic Claude Models

| Model | Cost (per 1K tokens) | Speed | Best For |
|-------|---------------------|-------|----------|
| **Claude 3 Opus** | $0.015 / $0.075 | Medium | Highest quality, complex tasks |
| **Claude 3 Sonnet** | $0.003 / $0.015 | Fast | Balanced cost/quality ⭐ |
| **Claude 3 Haiku** | $0.00025 / $0.00125 | Very Fast | High volume, low cost |

#### Ollama (Local)

| Model | Cost | Speed | Best For |
|-------|------|-------|----------|
| **Llama2** | FREE | Medium | General purpose, development |
| **Mistral** | FREE | Fast | Balanced performance |
| **CodeLlama** | FREE | Medium | Code generation |

---

## Configuration Options

### Option 1: Single Provider (Simple)

Use one provider for everything:

```bash
# .env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

### Option 2: Per-Module Configuration (Advanced)

Use different providers for different tasks:

```bash
# .env

# Default provider
LLM_PROVIDER=ollama
LLM_MODEL=llama2

# OpenAI for analysis (fast, cheap)
ANALYZER_LLM_PROVIDER=openai
ANALYZER_LLM_MODEL=gpt-3.5-turbo

# Anthropic for scoring (high quality)
SCORER_LLM_PROVIDER=anthropic
SCORER_LLM_MODEL=claude-3-sonnet-20240229

# OpenAI GPT-4 for response generation (best quality)
RESPONSE_LLM_PROVIDER=openai
RESPONSE_LLM_MODEL=gpt-4-turbo-preview

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Cost Optimization Example**:
- Analysis: GPT-3.5 (~$0.001 per opportunity)
- Scoring: Claude Sonnet (~$0.005 per opportunity)
- Response: GPT-4-turbo (~$0.02 per opportunity)
- **Total**: ~$0.026 per opportunity vs ~$0.06 with GPT-4 everywhere

**60% cost savings!** 💰

---

## Provider Setup

### OpenAI Setup

1. **Get API Key**
   ```bash
   # Visit: https://platform.openai.com/api-keys
   # Create new API key
   ```

2. **Configure**
   ```bash
   # .env
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4-turbo-preview  # or gpt-4, gpt-3.5-turbo
   OPENAI_API_KEY=sk-...
   ```

3. **Available Models**
   - `gpt-4` - Best quality, highest cost
   - `gpt-4-turbo-preview` - Fast, good quality, lower cost ⭐
   - `gpt-3.5-turbo` - Fastest, cheapest, good for simple tasks
   - `gpt-3.5-turbo-16k` - Longer context

### Anthropic Setup

1. **Get API Key**
   ```bash
   # Visit: https://console.anthropic.com/
   # Create API key
   ```

2. **Configure**
   ```bash
   # .env
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-3-sonnet-20240229
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Available Models**
   - `claude-3-opus-20240229` - Highest intelligence
   - `claude-3-sonnet-20240229` - Balanced cost/quality ⭐
   - `claude-3-haiku-20240307` - Fastest, most economical

### Ollama Setup (Local)

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Windows
   # Download from https://ollama.com/download
   ```

2. **Pull Model**
   ```bash
   ollama pull llama2
   # Or: mistral, codellama, neural-chat, etc.
   ```

3. **Start Server**
   ```bash
   ollama serve
   ```

4. **Configure**
   ```bash
   # .env
   LLM_PROVIDER=ollama
   LLM_MODEL=llama2
   OLLAMA_URL=http://localhost:11434
   ```

---

## Usage Examples

### Using in Code

```python
from app.llm import get_llm_provider

# Get default provider from config
llm = get_llm_provider()
response = await llm.complete("Analyze this job posting: ...")

# Switch providers programmatically
openai_llm = get_llm_provider("openai", "gpt-4")
claude_llm = get_llm_provider("anthropic", "claude-3-sonnet-20240229")
ollama_llm = get_llm_provider("ollama", "llama2")

# Use specific provider
response = await openai_llm.complete("Analyze...")
```

### Per-Module Configuration

```python
from app.llm.factory import get_module_provider

# Get provider configured for specific module
analyzer_llm = get_module_provider("analyzer")  # Uses ANALYZER_LLM_*
scorer_llm = get_module_provider("scorer")      # Uses SCORER_LLM_*
response_llm = get_module_provider("response_generator")  # Uses RESPONSE_LLM_*
```

### DSPy Integration

The system automatically configures DSPy with your chosen provider:

```python
from app.dspy_modules.pipeline import configure_dspy, get_pipeline

# Configure with default provider
configure_dspy()

# Or specify provider
configure_dspy(provider_type="anthropic", model_name="claude-3-sonnet-20240229")

# Get pipeline (uses configured provider)
pipeline = get_pipeline()
result = pipeline.forward(message="...", recruiter_name="...", profile=...)
```

---

## Cost Tracking

### Automatic Tracking

All LLM calls are automatically tracked with Prometheus metrics:

```bash
# View metrics
curl http://localhost:8000/api/v1/metrics | grep llm

# Metrics available:
# - llm_provider_requests_total{provider, model, status}
# - llm_provider_latency_seconds{provider, model}
# - llm_tokens_used_total{provider, model, type}
# - llm_cost_usd_total{provider, model}
# - llm_errors_total{provider, error_type}
```

### View in Grafana

```bash
# Access Grafana
open http://localhost:3000

# View "LLM Cost Tracking" dashboard
# Shows:
# - Cost per provider
# - Tokens used per provider
# - Cost trends over time
# - Most expensive operations
```

### Query Cost Data

```promql
# Total cost by provider (last 24h)
sum by (provider) (increase(llm_cost_usd_total[24h]))

# Average cost per request
sum(increase(llm_cost_usd_total[1h])) / sum(increase(llm_provider_requests_total[1h]))

# Cost breakdown by model
sum by (model) (increase(llm_cost_usd_total[24h]))
```

---

## Optimization Strategies

### Strategy 1: Tiered Approach

Use cheaper models for initial processing, expensive for important tasks:

```bash
# Fast/cheap for analysis
ANALYZER_LLM_PROVIDER=openai
ANALYZER_LLM_MODEL=gpt-3.5-turbo

# Medium for scoring
SCORER_LLM_PROVIDER=anthropic
SCORER_LLM_MODEL=claude-3-haiku

# Best quality for responses (user-facing)
RESPONSE_LLM_PROVIDER=openai
RESPONSE_LLM_MODEL=gpt-4
```

**Savings**: ~50-70% vs using GPT-4 everywhere

### Strategy 2: A/B Testing

Compare quality vs cost:

```python
# Test different models for same task
results_gpt4 = await test_with_model("openai", "gpt-4")
results_claude = await test_with_model("anthropic", "claude-3-sonnet")
results_gpt35 = await test_with_model("openai", "gpt-3.5-turbo")

# Compare quality and cost
# Choose best value-for-money
```

### Strategy 3: Fallback Chain

Primary → Fallback → Local:

```python
from app.llm import get_llm_provider

providers = [
    ("openai", "gpt-4"),
    ("anthropic", "claude-3-sonnet"),
    ("ollama", "llama2"),
]

for provider_type, model in providers:
    try:
        llm = get_llm_provider(provider_type, model)
        response = await llm.complete(prompt)
        break
    except Exception as e:
        logger.warning(f"Provider {provider_type} failed, trying next...")
        continue
```

---

## Monitoring & Observability

### Metrics Dashboard

Key metrics to monitor:

1. **Request Rate**: `llm_provider_requests_total`
2. **Latency**: `llm_provider_latency_seconds`
3. **Cost**: `llm_cost_usd_total`
4. **Errors**: `llm_errors_total`
5. **Token Usage**: `llm_tokens_used_total`

### Alerts to Configure

```yaml
# prometheus/alerts.yml

- alert: HighLLMCost
  expr: increase(llm_cost_usd_total[1h]) > 10
  labels:
    severity: warning
  annotations:
    summary: "High LLM cost detected"
    description: "LLM cost exceeded $10/hour"

- alert: LLMProviderDown
  expr: rate(llm_errors_total[5m]) > 0.1
  labels:
    severity: critical
  annotations:
    summary: "LLM provider errors detected"
```

---

## Troubleshooting

### Issue: Authentication Failed

**OpenAI**:
```bash
# Error: "Incorrect API key provided"
# Solution: Verify API key
echo $OPENAI_API_KEY
# Visit: https://platform.openai.com/api-keys
```

**Anthropic**:
```bash
# Error: "Invalid API key"
# Solution: Verify API key format starts with sk-ant-
echo $ANTHROPIC_API_KEY
```

### Issue: Rate Limits

```python
# Error: "Rate limit exceeded"
# Solutions:
# 1. Switch to different provider
# 2. Add retry logic (built-in)
# 3. Reduce request rate
# 4. Upgrade API plan
```

### Issue: Ollama Not Responding

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Verify model is pulled
ollama list
```

### Issue: High Costs

```bash
# Check cost metrics
curl http://localhost:8000/api/v1/metrics | grep llm_cost

# Identify expensive operations
# View in Grafana: LLM Cost dashboard

# Solutions:
# 1. Switch to cheaper models for non-critical tasks
# 2. Enable caching (reduces repeat calls)
# 3. Reduce max_tokens
# 4. Use per-module configuration
```

---

## Best Practices

### 1. Start with Ollama

```bash
# Develop with free local models
LLM_PROVIDER=ollama
LLM_MODEL=llama2
```

Benefits:
- ✅ Zero cost
- ✅ No rate limits
- ✅ Works offline
- ✅ Privacy (data stays local)

### 2. Use Per-Module Config for Production

```bash
# Optimize cost/quality balance
ANALYZER_LLM_MODEL=gpt-3.5-turbo  # Fast, cheap
SCORER_LLM_MODEL=claude-3-sonnet  # Balanced
RESPONSE_LLM_MODEL=gpt-4          # Best quality
```

### 3. Monitor Costs

- Set up Grafana dashboards
- Configure cost alerts
- Review monthly usage
- Test cheaper alternatives

### 4. Enable Caching

Caching (from Sprint 2) dramatically reduces costs:

```bash
# Ensure caching is enabled
CACHE_ENABLED=true
CACHE_TTL=3600

# Result: 60% reduction in LLM calls
```

### 5. Set Reasonable Limits

```bash
LLM_MAX_TOKENS=500  # Prevent runaway costs
LLM_TEMPERATURE=0.7  # Balance creativity/consistency
```

---

## Migration Guide

### From Ollama-only to Multi-Provider

**Before** (Sprint 1-2):
```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**After** (Sprint 3):
```bash
# Add new config
LLM_PROVIDER=ollama  # or openai, anthropic
LLM_MODEL=llama2

# Keep Ollama config for backwards compatibility
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Add API keys for cloud providers (optional)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

**No code changes needed!** The system is backwards compatible.

---

## FAQ

**Q: Which provider should I use?**

A: Depends on your needs:
- **Development**: Ollama (free, local)
- **Production (cost-sensitive)**: Claude Haiku or GPT-3.5
- **Production (quality)**: Claude Sonnet or GPT-4-turbo
- **Production (best)**: GPT-4 or Claude Opus

**Q: Can I mix providers?**

A: Yes! Use per-module configuration:
```bash
ANALYZER_LLM_PROVIDER=openai
SCORER_LLM_PROVIDER=anthropic
RESPONSE_LLM_PROVIDER=openai
```

**Q: How much does it cost?**

A: Typical costs per opportunity:
- GPT-3.5: ~$0.002
- Claude Haiku: ~$0.001
- Claude Sonnet: ~$0.01
- GPT-4: ~$0.05
- Ollama: FREE

**Q: Is my data secure?**

A:
- **OpenAI/Anthropic**: Data sent to cloud, encrypted in transit
- **Ollama**: Data stays on your server, fully private

**Q: Can I use my own models?**

A: Yes, with Ollama:
```bash
# Create custom model
ollama create mymodel -f Modelfile

# Use it
LLM_PROVIDER=ollama
LLM_MODEL=mymodel
```

---

## Next Steps

1. **Try Different Providers**: Test quality for your use case
2. **Optimize Costs**: Use per-module configuration
3. **Monitor Usage**: Set up Grafana dashboards
4. **Configure Alerts**: Get notified of issues
5. **Review Sprint 3.2**: Advanced search & filtering

---

## Support

- **Documentation**: `docs/`
- **Configuration**: `.env.example`
- **Metrics**: http://localhost:8000/api/v1/metrics
- **Dashboards**: http://localhost:3000 (Grafana)
- **Issues**: GitHub Issues

---

*Last Updated: January 18, 2024*
*Feature: Sprint 3.1 - Multi-Model LLM Support*
*Version: 1.2.0*
