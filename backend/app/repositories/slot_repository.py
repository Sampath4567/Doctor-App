from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.slot import Slot


class SlotRepository:
    """
    Data access helpers for Slot entities.
    """

    def get_for_update(self, db: Session, slot_id: int) -> Optional[Slot]:
        """
        Load a slot row and acquire a row-level lock.

        This uses SELECT ... FOR UPDATE to prevent concurrent modifications
        during booking/cancellation flows.
        """

        return (
            db.query(Slot)
            .with_for_update()
            .filter(Slot.id == slot_id)
            .one_or_none()
        )


slot_repository = SlotRepository()

