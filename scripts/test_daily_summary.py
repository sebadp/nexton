#!/usr/bin/env python3
"""
Test script para enviar email de resumen diario con datos de prueba.
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models import Opportunity
from app.notifications.service import NotificationService


async def test_daily_summary():
    """Test daily summary email with fake data."""

    # Create fake opportunities
    opportunities = [
        Opportunity(
            id=1,
            recruiter_name="María González",
            raw_message="Hola! Tenemos una posición de Senior Python Engineer...",
            company="TechCorp",
            role="Senior Python Engineer",
            seniority="Senior",
            tech_stack=["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
            salary_min=100000,
            salary_max=120000,
            currency="USD",
            remote_policy="Remote",
            location="Remote",
            tech_stack_score=35,
            salary_score=25,
            seniority_score=18,
            company_score=8,
            total_score=86,
            tier="HIGH_PRIORITY",
            ai_response="""Hola María,

Muchas gracias por contactarme. La posición de Senior Python Engineer en TechCorp definitivamente me interesa mucho.

Tengo más de 5 años de experiencia trabajando con Python, FastAPI y PostgreSQL, exactamente el stack que están buscando. Me especializo en desarrollo backend escalable y arquitecturas cloud-native.

¿Podrías compartirme más detalles sobre el proyecto y el equipo? Me gustaría saber más sobre los desafíos técnicos que están enfrentando.

Quedo atento a tu respuesta.

Saludos,
Sebastian""",
            status="processed",
            processing_time_ms=1500,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Opportunity(
            id=2,
            recruiter_name="Juan Pérez",
            raw_message="Te contacto para una posición de Staff Engineer...",
            company="StartupAI",
            role="Staff Engineer",
            seniority="Staff",
            tech_stack=["Python", "Django", "React", "AWS", "Kubernetes"],
            salary_min=130000,
            salary_max=150000,
            currency="USD",
            remote_policy="Hybrid",
            location="San Francisco, CA",
            tech_stack_score=32,
            salary_score=28,
            seniority_score=20,
            company_score=7,
            total_score=87,
            tier="HIGH_PRIORITY",
            ai_response="""Hola Juan,

Gracias por tu mensaje. La posición de Staff Engineer en StartupAI suena muy interesante.

Tengo experiencia liderando equipos técnicos y diseñando arquitecturas escalables. Mi background incluye Python/Django y deployment en AWS con Kubernetes.

Me gustaría conocer más sobre los proyectos de IA en los que están trabajando y cómo sería mi rol en el equipo.

¿Podríamos agendar una llamada esta semana?

Saludos,
Sebastian""",
            status="processed",
            processing_time_ms=1800,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Opportunity(
            id=3,
            recruiter_name="Ana Martínez",
            raw_message="Posición de Backend Developer en fintech...",
            company="FinTechCo",
            role="Backend Developer",
            seniority="Mid-Senior",
            tech_stack=["Python", "FastAPI", "MongoDB", "Kafka"],
            salary_min=80000,
            salary_max=100000,
            currency="USD",
            remote_policy="Remote",
            location="Remote - LATAM",
            tech_stack_score=28,
            salary_score=20,
            seniority_score=15,
            company_score=6,
            total_score=69,
            tier="INTERESANTE",
            ai_response="""Hola Ana,

Gracias por contactarme sobre la posición en FinTechCo.

Tengo experiencia con FastAPI y sistemas de mensajería como Kafka. El proyecto de fintech suena interesante, aunque me gustaría conocer más detalles sobre el rango salarial y el stack técnico específico.

¿Podrías compartir más información sobre el equipo y los desafíos técnicos?

Saludos,
Sebastian""",
            status="processed",
            processing_time_ms=1200,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    # Send daily summary
    service = NotificationService()
    result = await service.send_daily_summary(opportunities)

    if result:
        print("✅ Daily summary sent successfully!")
        print(f"📧 Email sent to: sebastian.davila.personal@gmail.com")
        print(f"📊 Opportunities included: {len(opportunities)}")
        print(f"\n🌐 View the email at: http://localhost:8025")
    else:
        print("❌ Failed to send daily summary")

    return result


if __name__ == "__main__":
    result = asyncio.run(test_daily_summary())
    sys.exit(0 if result else 1)
