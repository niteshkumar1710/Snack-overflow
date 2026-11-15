import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.idempotency import IdempotencyRecord
from app.utils.errors import AppException

IDEMPOTENCY_EXPIRATION_HOURS = 24


class IdempotencyService:
    """Service providing distributed database-level idempotency protection."""

    @staticmethod
    def generate_fingerprint(method: str, path: str, payload: Any) -> str:
        """Create a SHA-256 fingerprint from the request method, path, and payload."""
        if isinstance(payload, dict):
            serialized = json.dumps(payload, sort_keys=True)
        else:
            serialized = str(payload)
        raw_key = f"{method.upper()}:{path}:{serialized}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def start_operation(
        db: Session,
        user_id: int,
        key: str,
        fingerprint: str,
    ) -> Tuple[Optional[IdempotencyRecord], Optional[Dict[str, Any]]]:
        """Verify or create an idempotency record for the incoming request.

        Returns:
            Tuple of (record, cached_response_data)
            If cached_response_data is not None, the operation was already completed
            and the cached response should be returned immediately.

        Raises:
            AppException(409): If an operation with the same key is currently pending
                               or if the key is reused with a different request payload.
        """
        now = datetime.now(timezone.utc)

        # Query existing record for this user and key
        record = (
            db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.key == key,
            )
            .first()
        )

        if record:
            # Check for expiration: if expired, delete and allow fresh execution
            expires_at = record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < now:
                db.delete(record)
                db.commit()
                record = None
            else:
                # Validate payload fingerprint
                if record.request_fingerprint != fingerprint:
                    raise AppException(
                        status_code=409,
                        code="IDEMPOTENCY_KEY_PAYLOAD_MISMATCH",
                        message="Idempotency key was previously used with a different request payload.",
                    )

                if record.status == "pending":
                    raise AppException(
                        status_code=409,
                        code="OPERATION_IN_PROGRESS",
                        message="An operation with this idempotency key is currently processing. Please retry shortly.",
                    )

                if record.status == "completed":
                    cached_data = json.loads(record.response_body) if record.response_body else {}
                    return record, cached_data

                # If status is failed, allow the client to retry cleanly
                if record.status == "failed":
                    db.delete(record)
                    db.commit()
                    record = None

        # Insert a new pending record
        expires_at = now + timedelta(hours=IDEMPOTENCY_EXPIRATION_HOURS)
        new_record = IdempotencyRecord(
            user_id=user_id,
            key=key,
            request_fingerprint=fingerprint,
            status="pending",
            expires_at=expires_at,
        )
        db.add(new_record)
        try:
            db.commit()
            db.refresh(new_record)
            return new_record, None
        except IntegrityError:
            # Concurrent request inserted the same (user_id, key) simultaneously
            db.rollback()
            existing = (
                db.query(IdempotencyRecord)
                .filter(
                    IdempotencyRecord.user_id == user_id,
                    IdempotencyRecord.key == key,
                )
                .first()
            )
            if existing and existing.status == "completed" and existing.request_fingerprint == fingerprint:
                return existing, json.loads(existing.response_body) if existing.response_body else {}

            raise AppException(
                status_code=409,
                code="OPERATION_IN_PROGRESS",
                message="An operation with this idempotency key is currently processing. Please retry shortly.",
            )

    @staticmethod
    def complete_operation(
        db: Session,
        record_id: int,
        status_code: int,
        response_data: Dict[str, Any],
    ) -> None:
        """Mark the idempotency record as completed and store the response body."""
        db.query(IdempotencyRecord).filter(IdempotencyRecord.id == record_id).update(
            {
                "status": "completed",
                "response_status_code": status_code,
                "response_body": json.dumps(response_data),
            }
        )
        db.commit()

    @staticmethod
    def fail_operation(
        db: Session,
        record_id: int,
    ) -> None:
        """Mark the idempotency record as failed so subsequent attempts can retry."""
        try:
            db.query(IdempotencyRecord).filter(IdempotencyRecord.id == record_id).update(
                {"status": "failed"}
            )
            db.commit()
        except Exception:
            db.rollback()
