import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Mock data
MOCK_OPPORTUNITY = {
    "recruiter_name": "Test Recruiter",
    "raw_message": "Hola! Buscamos un Senior Python Dev. Salario $100k. Remoto.",
}


@pytest.mark.asyncio
async def test_feedback_loop(client: AsyncClient, db_session: AsyncSession):
    # 1. Create an opportunity
    response = await client.post("/api/v1/opportunities", json=MOCK_OPPORTUNITY)
    assert response.status_code == 201
    data = response.json()
    opportunity_id = data["id"]

    # Verify initial state
    assert data["feedback_score"] is None
    assert data["feedback_notes"] is None

    # 2. Add Feedback (Like)
    feedback_data = {
        "feedback_score": 1,
        "feedback_notes": "Great analysis, correct extraction.",
    }

    response = await client.patch(f"/api/v1/opportunities/{opportunity_id}", json=feedback_data)
    assert response.status_code == 200
    updated_data = response.json()

    # Verify feedback is stored
    assert updated_data["feedback_score"] == 1
    assert updated_data["feedback_notes"] == "Great analysis, correct extraction."

    # 3. Update Feedback (Change to Dislike)
    feedback_update = {
        "feedback_score": -1,
        "feedback_notes": "Actually, looking closer, the salary was wrong.",
    }

    response = await client.patch(f"/api/v1/opportunities/{opportunity_id}", json=feedback_update)
    assert response.status_code == 200
    final_data = response.json()

    assert final_data["feedback_score"] == -1
    assert final_data["feedback_notes"] == "Actually, looking closer, the salary was wrong."
