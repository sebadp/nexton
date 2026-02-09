"""
Scraping service for lite mode.

Provides synchronous scraping without Celery/Redis dependencies.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.scraper import LinkedInScraper, ScraperConfig

logger = get_logger(__name__)


class ScrapingService:
    """
    Scraping service for lite mode.

    Runs LinkedIn scraping synchronously without Celery background tasks.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize scraping service.

        Args:
            db: Database session
        """
        self.db = db
        self._scraper: LinkedInScraper | None = None

    async def scrape_sync(
        self,
        limit: int = 10,
        unread_only: bool = True,
    ) -> dict[str, Any]:
        """
        Run scraping synchronously (for lite mode).

        Args:
            limit: Maximum messages to scrape
            unread_only: Only scrape unread messages

        Returns:
            Dictionary with scraping results
        """
        logger.info(
            "lite_mode_scraping_started",
            limit=limit,
            unread_only=unread_only,
        )

        start_time = datetime.utcnow()
        results: dict[str, Any] = {
            "status": "started",
            "messages_found": 0,
            "messages_processed": 0,
            "opportunities_created": 0,
            "errors": [],
        }
        errors: list[str] = results["errors"]

        try:
            # Initialize scraper
            config = ScraperConfig(
                email=settings.LINKEDIN_EMAIL,
                password=settings.LINKEDIN_PASSWORD,
                headless=settings.SCRAPER_HEADLESS,
            )

            self._scraper = LinkedInScraper(config)
            await self._scraper.initialize()

            # Scrape messages
            logger.info("lite_mode_scraping_messages")
            messages = await self._scraper.scrape_messages(
                limit=limit,
                unread_only=unread_only,
            )

            results["messages_found"] = len(messages)
            logger.info("lite_mode_messages_found", count=len(messages))

            if not messages:
                results["status"] = "no_messages"
                results["message"] = "No hay mensajes nuevos sin leer en LinkedIn."
                return results

            # Process each message through the pipeline
            from app.services.opportunity_service import OpportunityService

            service = OpportunityService(self.db, cache=None)  # No cache in lite mode

            for msg in messages:
                try:
                    logger.info(
                        "lite_mode_processing_message",
                        sender=msg.sender_name,
                    )

                    opportunity = await service.create_opportunity(
                        recruiter_name=msg.sender_name,
                        raw_message=msg.message_text,
                        message_timestamp=msg.timestamp,
                        use_cache=False,  # No Redis cache in lite mode
                    )

                    results["messages_processed"] = int(results["messages_processed"]) + 1
                    results["opportunities_created"] = int(results["opportunities_created"]) + 1

                    logger.info(
                        "lite_mode_opportunity_created",
                        opportunity_id=opportunity.id,
                        score=opportunity.total_score,
                        tier=opportunity.tier,
                    )

                except Exception as e:
                    error_msg = f"Failed to process message from {msg.sender_name}: {str(e)}"
                    logger.error("lite_mode_processing_error", error=error_msg)
                    errors.append(error_msg)

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            results["status"] = "success"
            results["duration_seconds"] = duration

            # Build user-friendly message
            opps_created = results["opportunities_created"]
            if opps_created == 0:
                results["message"] = "Scraping completado pero no se crearon oportunidades."
            elif opps_created == 1:
                results["message"] = "✅ Scraping completado. Se creó 1 nueva oportunidad."
            else:
                results[
                    "message"
                ] = f"✅ Scraping completado. Se crearon {opps_created} nuevas oportunidades."

            logger.info(
                "lite_mode_scraping_completed",
                messages_found=results["messages_found"],
                messages_processed=results["messages_processed"],
                opportunities_created=results["opportunities_created"],
                duration_seconds=duration,
            )

            return results

        except Exception as e:
            logger.error("lite_mode_scraping_failed", error=str(e))
            results["status"] = "error"
            results["error"] = str(e)

            # Provide user-friendly error messages
            error_str = str(e).lower()
            if "login" in error_str or "credentials" in error_str:
                results[
                    "message"
                ] = "❌ Error de autenticación: No se pudo iniciar sesión en LinkedIn. Verifica tus credenciales."
            elif "timeout" in error_str:
                results[
                    "message"
                ] = "❌ LinkedIn no respondió a tiempo. Intenta de nuevo más tarde."
            elif "session" in error_str or "cookie" in error_str:
                results["message"] = "❌ La sesión de LinkedIn expiró. Intenta de nuevo."
            else:
                results["message"] = f"❌ Error durante el scraping: {str(e)}"

            return results

        finally:
            # Cleanup scraper
            if self._scraper:
                await self._scraper.cleanup()
                self._scraper = None

    async def scrape_with_progress(
        self,
        limit: int = 10,
        unread_only: bool = True,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Run scraping with progress events for SSE streaming.

        Yields progress events during each phase:
        - started: Initial event
        - progress: Step updates (login, scraping, analyzing)
        - opportunity_created: When an opportunity is saved
        - completed/error: Final event

        Args:
            limit: Maximum messages to scrape
            unread_only: Only scrape unread messages

        Yields:
            Progress event dictionaries
        """
        logger.info("sse_scraping_started", limit=limit, unread_only=unread_only)
        start_time = datetime.utcnow()

        yield {
            "event": "started",
            "message": "Iniciando scraping de LinkedIn...",
        }

        try:
            # Initialize scraper
            yield {
                "event": "progress",
                "step": "login",
                "message": "Conectando a LinkedIn...",
            }

            config = ScraperConfig(
                email=settings.LINKEDIN_EMAIL,
                password=settings.LINKEDIN_PASSWORD,
                headless=settings.SCRAPER_HEADLESS,
            )
            self._scraper = LinkedInScraper(config)
            await self._scraper.initialize()

            yield {
                "event": "progress",
                "step": "login",
                "status": "done",
                "message": "✓ Conectado a LinkedIn",
            }

            # Scrape messages
            yield {
                "event": "progress",
                "step": "scraping",
                "message": "Buscando mensajes...",
            }

            messages = await self._scraper.scrape_messages(
                limit=limit,
                unread_only=unread_only,
            )

            if not messages:
                yield {
                    "event": "completed",
                    "status": "no_messages",
                    "message": "No hay mensajes nuevos sin leer en LinkedIn.",
                    "opportunities_created": 0,
                }
                return

            yield {
                "event": "progress",
                "step": "scraping",
                "status": "done",
                "message": f"✓ Encontrados {len(messages)} mensajes",
                "count": len(messages),
            }

            # Process each message
            from app.services.opportunity_service import OpportunityService

            service = OpportunityService(self.db, cache=None)
            opportunities_created = 0
            errors: list[str] = []

            for i, msg in enumerate(messages, 1):
                yield {
                    "event": "progress",
                    "step": "analyzing",
                    "current": i,
                    "total": len(messages),
                    "message": f"Analizando mensaje {i}/{len(messages)}: {msg.sender_name}...",
                    "sender": msg.sender_name,
                }

                try:
                    # Create queue for progress updates from threadpool
                    queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()
                    loop = asyncio.get_running_loop()

                    def on_progress(
                        step: str,
                        data: dict,
                        loop: asyncio.AbstractEventLoop = loop,
                        queue: asyncio.Queue[tuple[str, dict]] = queue,
                    ) -> None:
                        loop.call_soon_threadsafe(queue.put_nowait, (step, data))

                    # Start opportunity creation in background task
                    task = asyncio.create_task(
                        service.create_opportunity(
                            recruiter_name=msg.sender_name,
                            raw_message=msg.message_text,
                            message_timestamp=msg.timestamp,
                            use_cache=False,
                            on_progress=on_progress,
                        )
                    )

                    # Process progress events while task is running or queue has items
                    while not task.done() or not queue.empty():
                        try:
                            # Wait for next event or small timeout
                            # If task is done, don't wait long (queue.get will return immediately if has items)
                            timeout = 0.1
                            step_name, step_data = await asyncio.wait_for(
                                queue.get(), timeout=timeout
                            )

                            # Map pipeline steps to user-friendly messages
                            message_text = f"Analizando mensaje {i}/{len(messages)}..."

                            if step_name == "conversation_state":
                                message_text = "Analizando tipo de mensaje..."
                            elif step_name == "extracting":
                                message_text = "Extrayendo datos clave (Empresa, Rol)..."
                            elif step_name == "extracted":
                                company = step_data.get("company", "Unknown")
                                role = step_data.get("role", "Unknown")
                                message_text = f"Datos extraídos: {company} - {role}"
                            elif step_name == "scoring":
                                message_text = "Calculando relevancia y puntaje..."
                            elif step_name == "scored":
                                score = step_data.get("total_score", 0)
                                message_text = f"Puntaje calculado: {score}/100"
                            elif step_name == "filtering":
                                message_text = "Verificando filtros obligatorios..."
                            elif step_name == "filtered":
                                message_text = "Filtros verificados."
                            elif step_name == "drafting":
                                message_text = "Generando borrador de respuesta..."
                            elif step_name == "drafted":
                                length = step_data.get("response_length", 0)
                                message_text = f"Respuesta generada ({length} caracteres)."

                            yield {
                                "event": "progress",
                                "step": "analyzing",
                                "current": i,
                                "total": len(messages),
                                "message": message_text,
                                "sender": msg.sender_name,
                                "detail": step_data,
                            }
                        except asyncio.TimeoutError:
                            if task.done():
                                break
                            continue

                    # Get result or raise exception
                    opportunity = await task
                    opportunities_created += 1

                    yield {
                        "event": "opportunity_created",
                        "id": opportunity.id,
                        "company": opportunity.company or "Unknown",
                        "role": opportunity.role or "Unknown",
                        "score": opportunity.total_score,
                        "tier": opportunity.tier,
                        "message": f"✓ Oportunidad creada: {opportunity.company or 'Unknown'} ({opportunity.total_score}pts)",
                    }

                except Exception as e:
                    error_msg = f"Error procesando mensaje de {msg.sender_name}: {str(e)}"
                    logger.error("sse_processing_error", error=error_msg)
                    errors.append(error_msg)
                    yield {
                        "event": "error",
                        "step": "analyzing",
                        "message": f"⚠ Error: {msg.sender_name}",
                        "detail": str(e),
                    }

            # Final summary
            duration = (datetime.utcnow() - start_time).total_seconds()

            if opportunities_created == 0:
                final_message = "Scraping completado pero no se crearon oportunidades."
            elif opportunities_created == 1:
                final_message = "✅ Scraping completado. Se creó 1 nueva oportunidad."
            else:
                final_message = f"✅ Scraping completado. Se crearon {opportunities_created} nuevas oportunidades."

            yield {
                "event": "completed",
                "status": "success",
                "message": final_message,
                "opportunities_created": opportunities_created,
                "messages_found": len(messages),
                "duration_seconds": duration,
                "errors": errors if errors else None,
            }

        except Exception as e:
            logger.error("sse_scraping_failed", error=str(e))

            # User-friendly error messages
            error_str = str(e).lower()
            if "login" in error_str or "credentials" in error_str:
                message = "❌ Error de autenticación: No se pudo iniciar sesión en LinkedIn."
            elif "timeout" in error_str:
                message = "❌ LinkedIn no respondió a tiempo. Intenta de nuevo."
            elif "session" in error_str or "cookie" in error_str:
                message = "❌ La sesión de LinkedIn expiró."
            else:
                message = f"❌ Error durante el scraping: {str(e)}"

            yield {
                "event": "error",
                "status": "error",
                "message": message,
                "detail": str(e),
            }

        finally:
            if self._scraper:
                await self._scraper.cleanup()
                self._scraper = None
