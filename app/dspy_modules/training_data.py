"""
Training data for DSPy optimizers.

This module contains labeled examples for training different modules in the pipeline:
1. ConversationStateAnalyzer (conversation_state_trainset)
2. MessageAnalyzer (message_analysis_trainset)
3. FollowUpAnalyzer (follow_up_trainset)
"""
import dspy
from app.dspy_modules.models import ConversationState

# --- 1. ConversationStateAnalyzer Examples ---

conversation_state_raw_data = [
    # NEW_OPPORTUNITY cases
    {
        "message": "Hola Sebastián! Vi tu perfil y me parece muy interesante. Estamos buscando un Senior Backend Engineer para TechCorp, una empresa de AI/ML con sede en San Francisco. El puesto es 100% remoto, con un salario de $120,000-$150,000 USD anuales. Stack: Python, FastAPI, PostgreSQL, AWS. ¿Te interesaría saber más?",
        "conversation_state": "NEW_OPPORTUNITY",
        "contains_job_details": "YES",
        "confidence": "HIGH",
        "reasoning": "Message contains specific job details (role, company, salary, stack) and clearly proposes a new opportunity."
    },
    {
        "message": "Hola! Tenemos una posición de Python Developer en una consultora. Es presencial en Buenos Aires, 5 días a la semana. Salario: $50,000 USD. ¿Te interesa?",
        "conversation_state": "NEW_OPPORTUNITY",
        "contains_job_details": "YES",
        "confidence": "HIGH",
        "reasoning": "Clear job offer with role, location and salary details."
    },
    {
        "message": "Hi Sebastián, We have a Staff Engineer position at a 4-day work week company! Remote-first, $140,000-$180,000 USD, focused on AI/ML products. Tech: Python, LangChain, FastAPI, Kubernetes. Would you like to chat this week?",
        "conversation_state": "NEW_OPPORTUNITY",
        "contains_job_details": "YES",
        "confidence": "HIGH",
        "reasoning": "Detailed job opportunity with specific role and compensation info."
    },
    {
        "message": "Buenas tardes, te contacto de GlobalTech. Buscamos devs con tu perfil para sumarse a nuestro equipo de pagos. Trabajamos con Go y Python. Te adjunto JD.",
        "conversation_state": "NEW_OPPORTUNITY",
        "contains_job_details": "YES",
        "confidence": "HIGH",
        "reasoning": "Recruiter contacting for a specific role/team, mentions tech stack."
    },
    {
        "message": "Hola Sebastián, ¿cómo estás? Soy reclutadora en StartUp X. Me gustaría contarte sobre una vacante de Tech Lead que tenemos abierta. Es 100% remoto en USD.",
        "conversation_state": "NEW_OPPORTUNITY",
        "contains_job_details": "YES",
        "confidence": "HIGH",
        "reasoning": "Opening a conversation about a specific vacancy (Tech Lead)."
    },

    # COURTESY_CLOSE cases
    {
        "message": "Gracias por tu respuesta, quedamos en contacto!",
        "conversation_state": "COURTESY_CLOSE",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Standard polite closing phrase, no new information."
    },
    {
        "message": "Ok, perfecto",
        "conversation_state": "COURTESY_CLOSE",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Short acknowledgment."
    },
    {
        "message": "Muchas gracias, Sebastián. Te aviso cualquier cosa.",
        "conversation_state": "COURTESY_CLOSE",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Polite dismissal/closing."
    },
    {
        "message": "Dale, buenísimo. Hablamos la semana que viene.",
        "conversation_state": "COURTESY_CLOSE",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Scheduling/postponing conversation but effectively a closing for now."
    },
    {
        "message": "Entendido, gracias por la aclaración.",
        "conversation_state": "COURTESY_CLOSE",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Acknowledgment of previous message."
    },

    # FOLLOW_UP cases
    {
        "message": "Sure, Sebastián! mandame si queres un mensajito",
        "conversation_state": "FOLLOW_UP",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Response to candidate's previous interaction, continuing codeversation."
    },
    {
        "message": "Gracias por tu interés! ¿Cuál es tu expectativa salarial?",
        "conversation_state": "FOLLOW_UP",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Recruiter asking a specific follow-up question."
    },
    {
        "message": "Perfecto! ¿Cuándo podrías empezar si avanzamos con el proceso?",
        "conversation_state": "FOLLOW_UP",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Follow-up question about availability."
    },
    {
        "message": "Buenísimo! Te cuento más la semana que viene.",
        "conversation_state": "FOLLOW_UP",
        "contains_job_details": "NO",
        "confidence": "MEDIUM",
        "reasoning": "Continuing conversation, promising future info."
    },
    {
        "message": "¿Podrías tener una llamada mañana a las 14hs?",
        "conversation_state": "FOLLOW_UP",
        "contains_job_details": "NO",
        "confidence": "HIGH",
        "reasoning": "Scheduling request, part of ongoing conversation."
    }
]

conversation_state_trainset = [
    dspy.Example(
        message=ex["message"],
        conversation_state=ex["conversation_state"],
        expected_state=ex["conversation_state"], # For metric validation
        contains_job_details=ex["contains_job_details"],
        confidence=ex["confidence"],
        reasoning=ex["reasoning"]
    ).with_inputs("message")
    for ex in conversation_state_raw_data
]


# --- 2. MessageAnalyzer Examples ---

message_analysis_raw_data = [
    {
        "message": "Hola Sebastián! Vi tu perfil y me parece muy interesante. Estamos buscando un Senior Backend Engineer para TechCorp, una empresa de AI/ML con sede en San Francisco. El puesto es 100% remoto, con un salario de $120,000-$150,000 USD anuales. Stack: Python, FastAPI, PostgreSQL, AWS. ¿Te interesaría saber más?",
        "company": "TechCorp",
        "role": "Senior Backend Engineer",
        "seniority": "Senior",
        "tech_stack": "Python, FastAPI, PostgreSQL, AWS",
        "salary_range": "120000-150000 USD",
        "remote_policy": "Remote",
        "location": "San Francisco"
    },
    {
        "message": "Hola! Tenemos una posición de Python Developer en una consultora. Es presencial en Buenos Aires, 5 días a la semana. Salario: $50,000 USD. ¿Te interesa?",
        "company": "consultora",
        "role": "Python Developer",
        "seniority": "Unknown",
        "tech_stack": "Python",
        "salary_range": "50000 USD",
        "remote_policy": "Onsite",
        "location": "Buenos Aires"
    },
    {
        "message": "Hi Sebastián, We have a Staff Engineer position at a 4-day work week company! Remote-first, $140,000-$180,000 USD, focused on AI/ML products. Tech: Python, LangChain, FastAPI, Kubernetes.",
        "company": "Unknown",
        "role": "Staff Engineer",
        "seniority": "Staff",
        "tech_stack": "Python, LangChain, FastAPI, Kubernetes",
        "salary_range": "140000-180000 USD",
        "remote_policy": "Remote",
        "location": "Not specified"
    },
    {
        "message": "Buscamos un Tech Lead para MercadoLibre. Es para trabajar híbrido en oficinas de Saavedra. Stack requeridos: Java, Go, AWS. Salario competitivo en pesos.",
        "company": "MercadoLibre",
        "role": "Tech Lead",
        "seniority": "Senior", # Tech Lead usually implies Senior/Staff
        "tech_stack": "Java, Go, AWS",
        "salary_range": "Not mentioned",
        "remote_policy": "Hybrid",
        "location": "Saavedra"
    },
    {
        "message": "Opportunity: Full Stack Developer (React+Node) at StartupX. Rates up to $60/hr. 100% Remote, LATAM only.",
        "company": "StartupX",
        "role": "Full Stack Developer",
        "seniority": "Unknown",
        "tech_stack": "React, Node",
        "salary_range": "60 USD/hr", # Helper might need to convert this to verify
        "remote_policy": "Remote",
        "location": "LATAM"
    }
]

message_analysis_trainset = [
    dspy.Example(
        message=ex["message"],
        company=ex["company"],
        role=ex["role"],
        seniority=ex["seniority"],
        tech_stack=ex["tech_stack"],
        salary_range=ex["salary_range"],
        remote_policy=ex["remote_policy"],
        location=ex["location"]
    ).with_inputs("message")
    for ex in message_analysis_raw_data
]


# --- 3. FollowUpAnalyzer Examples ---

follow_up_raw_data = [
    {
        "message": "Gracias por tu interés! ¿Cuál es tu expectativa salarial?",
        "candidate_profile_summary": "Name: Seb. Salary expectation: $80,000 - $120,000 USD annually. Currently employed.",
        "question_type": "SALARY",
        "detected_question": "¿Cuál es tu expectativa salarial?",
        "can_auto_respond": "YES",
        "requires_context": "NO",
        "reasoning": "Clear question about salary which is present in profile."
    },
    {
        "message": "Perfecto! ¿Cuándo podrías empezar si avanzamos con el proceso?",
        "candidate_profile_summary": "Name: Seb. Currently employed: Yes. Notice period: 2-4 weeks.",
        "question_type": "AVAILABILITY",
        "detected_question": "¿Cuándo podrías empezar?",
        "can_auto_respond": "YES",
        "requires_context": "NO",
        "reasoning": "Question about start date/availability answersable with notice period."
    },
    {
        "message": "Sure, Sebastián! mandame si queres un mensajito",
        "candidate_profile_summary": "Name: Seb.",
        "question_type": "NONE",
        "detected_question": "N/A",
        "can_auto_respond": "NO",
        "requires_context": "YES",
        "reasoning": "No specific question, refers to previous context ('mandame un mensajito')."
    },
    {
        "message": "¿Podrías tener una llamada mañana a las 14hs?",
        "candidate_profile_summary": "Name: Seb.",
        "question_type": "SCHEDULING",
        "detected_question": "¿Podrías tener una llamada mañana a las 14hs?",
        "can_auto_respond": "NO",
        "requires_context": "NO",
        "reasoning": "Scheduling requires checking live calendar, cannot auto-respond safely."
    },
    {
        "message": "¿Cuántos años de experiencia tenés con Kubernetes?",
        "candidate_profile_summary": "Name: Seb. Experience: 5 years. Techs: Python, Kubernetes, AWS.",
        "question_type": "EXPERIENCE",
        "detected_question": "¿Cuántos años de experiencia tenés con Kubernetes?",
        "can_auto_respond": "YES",
        "requires_context": "NO",
        "reasoning": "Specific experience question answerable from profile techs and years."
    }
]

follow_up_trainset = [
    dspy.Example(
        message=ex["message"],
        candidate_profile_summary=ex["candidate_profile_summary"],
        question_type=ex["question_type"],
        detected_question=ex["detected_question"],
        can_auto_respond=ex["can_auto_respond"],
        requires_context=ex["requires_context"],
        reasoning=ex["reasoning"]
    ).with_inputs("message", "candidate_profile_summary")
    for ex in follow_up_raw_data
]
