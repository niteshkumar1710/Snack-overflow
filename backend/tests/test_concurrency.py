from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.snack import Snack
from app.models.activity import Activity
from app.database.connection import check_database_connection, SessionLocal
from app.services.consumption_service import consumption_service


def test_postgresql_concurrency_consumption():
    """CRITICAL CONCURRENCY TEST (PostgreSQL-backed).
    
    Assignment Specification:
    - Initial snack quantity is 3.
    - 10 independent requests attempt to consume 1 packet at approximately the same time.
    - Exactly 3 requests succeed (HTTP 200).
    - Exactly 7 requests receive HTTP 409 Conflict ('Someone beat you to the last packet!').
    - Final quantity in the database is exactly 0.
    - Exactly 3 consumed activity records are created.
    - Genuinely concurrent requests using separate database sessions/connections.
    - SQLite is NOT used as proof of concurrency behavior.
    """
    is_connected, msg = check_database_connection()
    if not is_connected:
        pytest.skip(
            f"PostgreSQL test database not connected ({msg}). "
            "To execute this live concurrency test, supply your Supabase PostgreSQL connection string in backend/.env."
        )

    # 1. Setup test fixture directly in PostgreSQL
    with SessionLocal() as setup_db:
        # Clean up any leftover test data
        setup_db.query(Snack).filter_by(name="PG Concurrent Snack").delete()
        setup_db.query(User).filter(User.email.like("pg_concurrent_%")).delete()
        setup_db.commit()

        # Create snack with quantity = 3
        snack = Snack(
            name="PG Concurrent Snack",
            category="savoury",
            quantity=3,
            low_stock_threshold=2,
        )
        setup_db.add(snack)

        # Create 10 distinct users
        users = []
        for i in range(10):
            u = User(
                name=f"PG User {i}",
                email=f"pg_concurrent_{i}@example.com",
                password_hash=hash_password("pw"),
                role="member",
            )
            setup_db.add(u)
            users.append(u)

        setup_db.commit()
        setup_db.refresh(snack)
        snack_id = snack.id
        user_ids = [u.id for u in users]

    # 2. Worker function executed simultaneously in separate threads
    def thread_worker_consume(user_id: int):
        # Each thread uses its own dedicated PostgreSQL session & connection
        with SessionLocal() as thread_db:
            user = thread_db.query(User).filter_by(id=user_id).first()
            try:
                snack_resp, act_resp = consumption_service.consume_snack(
                    db=thread_db,
                    snack_id=snack_id,
                    user=user,
                    amount=1,
                )
                return {
                    "status_code": 200,
                    "quantity": snack_resp.quantity,
                    "activity_id": act_resp.id,
                }
            except Exception as exc:
                status_code = getattr(exc, "status_code", 500)
                code = getattr(exc, "code", "UNKNOWN")
                return {
                    "status_code": status_code,
                    "code": code,
                    "error": str(exc),
                }

    # 3. Fire 10 simultaneous threads using ThreadPoolExecutor
    responses = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(thread_worker_consume, uid) for uid in user_ids]
        for future in as_completed(futures):
            responses.append(future.result())

    # 4. Analyze concurrency outcomes
    status_codes = [r["status_code"] for r in responses]
    success_count = status_codes.count(200)
    conflict_count = status_codes.count(409)

    assert success_count == 3, f"Expected exactly 3 successes, got {success_count}. Responses: {responses}"
    assert conflict_count == 7, f"Expected exactly 7 conflicts (409), got {conflict_count}. Responses: {responses}"

    # 5. Verify final PostgreSQL database state
    with SessionLocal() as verify_db:
        final_snack = verify_db.query(Snack).filter_by(id=snack_id).first()
        assert final_snack.quantity == 0, f"Expected final quantity to be exactly 0, got {final_snack.quantity}"
        assert final_snack.status == "gone"

        activities = verify_db.query(Activity).filter_by(snack_id=snack_id, action="consumed").all()
        assert len(activities) == 3, f"Expected exactly 3 consumed activities, found {len(activities)}"

        # Clean up test artifacts
        verify_db.delete(final_snack)
        verify_db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        verify_db.commit()
