import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.snack import Snack
from app.models.vote import Vote
from app.models.activity import Activity


# ---------------------------------------------------------------------------
# User Model Tests
# ---------------------------------------------------------------------------

def test_create_valid_user(db_session: Session):
    """Verify creating a user with valid attributes."""
    user = User(
        name="Alice Engineer",
        email="alice@example.com",
        password_hash="fakehash123",
        role="member",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.name == "Alice Engineer"
    assert user.email == "alice@example.com"
    assert user.role == "member"
    assert user.created_at is not None


def test_unique_user_email_constraint(db_session: Session):
    """Verify unique constraint on email prevents duplicates."""
    user1 = User(name="User 1", email="duplicate@example.com", password_hash="hash1")
    user2 = User(name="User 2", email="duplicate@example.com", password_hash="hash2")

    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invalid_user_role_constraint(db_session: Session):
    """Verify check constraint on role restricts values to 'admin' or 'member'."""
    invalid_user = User(
        name="Super User",
        email="superuser@example.com",
        password_hash="hash123",
        role="superadmin",  # Invalid role
    )
    db_session.add(invalid_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# Snack Model Tests & Status Calculation
# ---------------------------------------------------------------------------

def test_create_valid_snack(db_session: Session):
    """Verify creating a snack with valid attributes and default thresholds."""
    snack = Snack(
        name="Baked Pita Chips",
        category="savoury",
        quantity=20,
        low_stock_threshold=5,
    )
    db_session.add(snack)
    db_session.commit()
    db_session.refresh(snack)

    assert snack.id is not None
    assert snack.name == "Baked Pita Chips"
    assert snack.category == "savoury"
    assert snack.quantity == 20
    assert snack.low_stock_threshold == 5
    assert snack.status == "stocked"


def test_unique_snack_name_constraint(db_session: Session):
    """Verify unique constraint on snack name prevents duplicates."""
    snack1 = Snack(name="Kombucha", category="drink", quantity=10)
    snack2 = Snack(name="Kombucha", category="drink", quantity=5)

    db_session.add(snack1)
    db_session.commit()

    db_session.add(snack2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_non_negative_quantity_constraint(db_session: Session):
    """Verify check constraint prevents snack quantity from becoming negative."""
    invalid_snack = Snack(
        name="Negative Snack",
        category="sweet",
        quantity=-1,  # Prohibited by check constraint
    )
    db_session.add(invalid_snack)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invalid_snack_category_constraint(db_session: Session):
    """Verify check constraint restricts category to allowed values."""
    invalid_snack = Snack(
        name="Mystery Item",
        category="fast-food",  # Not in allowed categories
        quantity=5,
    )
    db_session.add(invalid_snack)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_derived_snack_status_rules(db_session: Session):
    """Verify dynamic status calculation:
    - 'stocked': quantity > low_stock_threshold
    - 'running_low': quantity > 0 and quantity <= low_stock_threshold
    - 'gone': quantity == 0
    """
    threshold = 5

    # Case 1: Stocked (qty > threshold)
    s1 = Snack(name="Stocked Snack", category="sweet", quantity=10, low_stock_threshold=threshold)
    assert s1.status == "stocked"

    # Case 2: Running low boundary (qty == threshold)
    s2 = Snack(name="Running Low Snack 1", category="drink", quantity=5, low_stock_threshold=threshold)
    assert s2.status == "running_low"

    # Case 3: Running low inner (0 < qty < threshold)
    s3 = Snack(name="Running Low Snack 2", category="healthy-ish", quantity=1, low_stock_threshold=threshold)
    assert s3.status == "running_low"

    # Case 4: Gone (qty == 0)
    s4 = Snack(name="Gone Snack", category="savoury", quantity=0, low_stock_threshold=threshold)
    assert s4.status == "gone"


# ---------------------------------------------------------------------------
# Vote Model Tests & Unique Constraint
# ---------------------------------------------------------------------------

def test_create_valid_vote(db_session: Session):
    """Verify a user can vote for a snack."""
    user = User(name="Voter 1", email="voter1@example.com", password_hash="hash")
    snack = Snack(name="Sparkling Water", category="drink", quantity=10)
    db_session.add_all([user, snack])
    db_session.commit()

    vote = Vote(user_id=user.id, snack_id=snack.id)
    db_session.add(vote)
    db_session.commit()
    db_session.refresh(vote)

    assert vote.id is not None
    assert vote.user_id == user.id
    assert vote.snack_id == snack.id
    assert vote.created_at is not None


def test_unique_user_snack_vote_constraint(db_session: Session):
    """Verify database-level unique constraint prevents a user from voting twice for the same snack."""
    user = User(name="Voter 2", email="voter2@example.com", password_hash="hash")
    snack = Snack(name="Dark Chocolate", category="sweet", quantity=15)
    db_session.add_all([user, snack])
    db_session.commit()

    vote1 = Vote(user_id=user.id, snack_id=snack.id)
    db_session.add(vote1)
    db_session.commit()

    # Attempt to vote a second time for the same snack
    vote2 = Vote(user_id=user.id, snack_id=snack.id)
    db_session.add(vote2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# Activity Model Tests & Action Constraints
# ---------------------------------------------------------------------------

def test_create_valid_activity(db_session: Session):
    """Verify logging a valid consumption activity."""
    user = User(name="Consumer", email="consumer@example.com", password_hash="hash")
    snack = Snack(name="Almonds", category="healthy-ish", quantity=30)
    db_session.add_all([user, snack])
    db_session.commit()

    act = Activity(user_id=user.id, snack_id=snack.id, action="consumed", amount=2)
    db_session.add(act)
    db_session.commit()
    db_session.refresh(act)

    assert act.id is not None
    assert act.action == "consumed"
    assert act.amount == 2
    assert act.created_at is not None


def test_invalid_activity_action_constraint(db_session: Session):
    """Verify check constraint restricts action to 'consumed' or 'restocked'."""
    user = User(name="Actor", email="actor@example.com", password_hash="hash")
    snack = Snack(name="Cashews", category="healthy-ish", quantity=10)
    db_session.add_all([user, snack])
    db_session.commit()

    invalid_act = Activity(user_id=user.id, snack_id=snack.id, action="damaged", amount=1)
    db_session.add(invalid_act)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_activity_positive_amount_constraint(db_session: Session):
    """Verify check constraint requires amount to be positive (> 0)."""
    user = User(name="Actor 2", email="actor2@example.com", password_hash="hash")
    snack = Snack(name="Walnuts", category="healthy-ish", quantity=10)
    db_session.add_all([user, snack])
    db_session.commit()

    invalid_act = Activity(user_id=user.id, snack_id=snack.id, action="consumed", amount=0)
    db_session.add(invalid_act)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# Cascade Deletion Strategy Tests
# ---------------------------------------------------------------------------

def test_cascade_deletion_on_snack_delete(db_session: Session):
    """Verify deleting a snack cascades to remove dependent votes and activities safely."""
    user = User(name="Charlie", email="charlie@example.com", password_hash="hash")
    snack = Snack(name="Pretzels", category="savoury", quantity=10)
    db_session.add_all([user, snack])
    db_session.commit()

    vote = Vote(user_id=user.id, snack_id=snack.id)
    activity = Activity(user_id=user.id, snack_id=snack.id, action="consumed", amount=1)
    db_session.add_all([vote, activity])
    db_session.commit()

    # Delete snack
    db_session.delete(snack)
    db_session.commit()

    # Verify votes and activities associated with this snack are deleted
    assert db_session.query(Vote).filter_by(snack_id=snack.id).first() is None
    assert db_session.query(Activity).filter_by(snack_id=snack.id).first() is None
    # User remains intact
    assert db_session.query(User).filter_by(id=user.id).first() is not None
