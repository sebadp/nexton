"""
Metrics for evaluating DSPy modules validation.

This module defines metric functions used by DSPy optimizers to evaluate
the quality of generated prompts and outputs.
"""
from app.core.logging import get_logger

logger = get_logger(__name__)


def validate_conversation_state(example, pred, trace=None):
    """
    Validate conversation state classification.
    
    Checks if the predicted state matches the expected state.
    """
    # Extract predicted state
    # Handle both string output (if raw) or pydantic model (if integrated)
    pred_state = getattr(pred, "conversation_state", None)
    
    # If pred is a Result object (like ConversationStateResult), get the state enum value
    if hasattr(pred_state, "state"):
        pred_state = pred_state.state.value
    elif hasattr(pred_state, "value"):
        pred_state = pred_state.value
        
    expected = example.expected_state
    
    # Check match
    matches = str(pred_state) == str(expected)
    
    if trace is None:
        return matches
        
    # Validation of 'contains_job_details' field if present
    details_match = True
    if hasattr(example, "contains_job_details") and hasattr(pred, "contains_job_details"):
        details_match = str(pred.contains_job_details).upper() == str(example.contains_job_details).upper()
        
    return matches and details_match


def validate_message_analysis(example, pred, trace=None):
    """
    Validate message analysis extraction.
    
    Checks accuracy of extracted fields: company, role, salary, etc.
    Returns a float score (0.0 to 1.0) based on field matches.
    """
    score = 0.0
    total_fields = 0
    
    fields_to_check = [
        "company", "role", "seniority", "remote_policy", "location"
    ]
    
    # 1. Check simple string fields
    for field in fields_to_check:
        if hasattr(example, field):
            total_fields += 1
            expected = getattr(example, field)
            predicted = getattr(pred, field, "")
            
            # Simple normalization for comparison
            if str(expected).lower().strip() == str(predicted).lower().strip():
                score += 1.0
            elif str(expected).lower() in str(predicted).lower():
                score += 0.5  # Partial match
                
    # 2. Check tech stack (list overlap)
    if hasattr(example, "tech_stack"):
        total_fields += 1
        expected_stack = [t.lower().strip() for t in example.tech_stack.split(",") if t.strip()] if isinstance(example.tech_stack, str) else example.tech_stack
        
        # Handle predicted stack (could be list or string)
        pred_stack = getattr(pred, "tech_stack", [])
        if isinstance(pred_stack, str):
            pred_stack = [t.lower().strip() for t in pred_stack.split(",") if t.strip()]
        else:
            pred_stack = [str(t).lower().strip() for t in pred_stack]
            
        # Calculate Jaccard similarity for tech stack
        set_exp = set(expected_stack)
        set_pred = set(pred_stack)
        
        if not set_exp and not set_pred:
            stack_score = 1.0
        elif not set_exp or not set_pred:
            stack_score = 0.0
        else:
            intersection = len(set_exp.intersection(set_pred))
            union = len(set_exp.union(set_pred))
            stack_score = intersection / union if union > 0 else 0.0
            
        score += stack_score

    # 3. Check salary (range overlap or value match)
    if hasattr(example, "salary_range"):
        total_fields += 1
        expected_salary = str(example.salary_range).lower()
        predicted_salary = str(getattr(pred, "salary_range", "")).lower()
        
        # Basic check: if "not mentioned" matches
        if "not mentioned" in expected_salary and ("not mentioned" in predicted_salary or not predicted_salary):
            score += 1.0
        # If both are numbers, check exact match (this logic could be more robust)
        elif expected_salary == predicted_salary:
            score += 1.0
        elif expected_salary in predicted_salary:
            score += 0.8
        else:
            # Check if numbers match at least
            import re
            nums_exp = re.findall(r'\d+', expected_salary)
            nums_pred = re.findall(r'\d+', predicted_salary)
            if nums_exp and nums_pred and set(nums_exp) == set(nums_pred):
                score += 0.9

    return score / total_fields if total_fields > 0 else 0.0


def validate_follow_up(example, pred, trace=None):
    """
    Validate follow-up analysis.
    
    Checks decision correctness (can_auto_respond) and question type.
    """
    matches = True
    
    # Check auto-respond decision (Critical)
    expected_auto = str(example.can_auto_respond).upper() == "YES"  # Normalize input
    
    # Handle pred (could be string "YES"/"NO" or boolean)
    pred_auto = getattr(pred, "can_auto_respond", "NO")
    if isinstance(pred_auto, str):
        pred_auto = pred_auto.upper() == "YES"
        
    if expected_auto != pred_auto:
        return False
        
    # Check question type if auto-response is YES
    if expected_auto:
        expected_type = str(example.question_type).upper()
        pred_type = str(getattr(pred, "question_type", "")).upper()
        
        if expected_type != pred_type:
            return False
            
    return True
