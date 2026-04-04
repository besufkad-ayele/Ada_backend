"""
Inventory Manager — Fare Class Fencing

Manages the open/close state of fare classes based on:
- Occupancy thresholds
- Lead time to arrival
- Demand forecasts
- Manual overrides

This mimics how airlines manage seat inventory.
"""
from datetime import date, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.rooms import DailyInventory, RoomType


settings = get_settings()


class InventoryManager:
    """
    Controls fare class availability.
    
    Rules:
    1. Saver class closes when occupancy > 60% OR less than 14 days out
    2. Standard class closes when occupancy > 85% OR less than 3 days out
    3. Premium class is always open (captures last-minute value)
    4. If forecast shows high demand, close lower classes earlier
    """

    # Auto-close thresholds
    SAVER_CLOSE_OCCUPANCY = 0.60
    SAVER_CLOSE_LEAD_TIME = 14  # Close saver within 14 days of arrival
    STANDARD_CLOSE_OCCUPANCY = 0.85
    STANDARD_CLOSE_LEAD_TIME = 3

    def __init__(self, db: Session):
        self.db = db

    def update_fare_classes(self, room_type_id: int, target_date: date) -> Dict:
        """
        Update fare class open/close status for a room type on a date.
        Returns the updated status.
        """
        inventory = self.db.query(DailyInventory).filter(
            DailyInventory.room_type_id == room_type_id,
            DailyInventory.date == target_date,
        ).first()

        if not inventory:
            return {"error": "No inventory record found"}

        lead_time = max(0, (target_date - date.today()).days)
        occupancy = inventory.occupancy_rate or 0.0
        forecast = inventory.forecasted_occupancy or occupancy

        # Use the higher of actual and forecasted for conservative fencing
        effective_occupancy = max(occupancy, forecast)

        changes = []

        # --- SAVER CLASS ---
        saver_was_open = inventory.saver_open
        saver_sold_out = inventory.saver_sold >= inventory.saver_total

        if saver_sold_out:
            inventory.saver_open = False
            if saver_was_open:
                changes.append("Saver class CLOSED — inventory sold out")
        elif effective_occupancy >= self.SAVER_CLOSE_OCCUPANCY:
            inventory.saver_open = False
            if saver_was_open:
                changes.append(
                    f"Saver class CLOSED — occupancy {effective_occupancy:.0%} "
                    f"exceeds {self.SAVER_CLOSE_OCCUPANCY:.0%} threshold"
                )
        elif lead_time < self.SAVER_CLOSE_LEAD_TIME:
            inventory.saver_open = False
            if saver_was_open:
                changes.append(
                    f"Saver class CLOSED — only {lead_time} days until arrival "
                    f"(threshold: {self.SAVER_CLOSE_LEAD_TIME} days)"
                )
        else:
            inventory.saver_open = True

        # --- STANDARD CLASS ---
        std_was_open = inventory.standard_open
        std_sold_out = inventory.standard_sold >= inventory.standard_total

        if std_sold_out:
            inventory.standard_open = False
            if std_was_open:
                changes.append("Standard class CLOSED — inventory sold out")
        elif effective_occupancy >= self.STANDARD_CLOSE_OCCUPANCY:
            inventory.standard_open = False
            if std_was_open:
                changes.append(
                    f"Standard class CLOSED — occupancy {effective_occupancy:.0%} "
                    f"exceeds {self.STANDARD_CLOSE_OCCUPANCY:.0%} threshold"
                )
        elif lead_time < self.STANDARD_CLOSE_LEAD_TIME:
            inventory.standard_open = False
            if std_was_open:
                changes.append(
                    f"Standard class CLOSED — only {lead_time} days until arrival"
                )
        else:
            inventory.standard_open = True

        # --- PREMIUM CLASS ---
        # Premium is ALWAYS open (last resort for revenue)
        inventory.premium_open = True

        # Update available rooms
        inventory.available_rooms = max(
            0, inventory.total_rooms - inventory.booked_rooms - inventory.blocked_rooms
        )

        self.db.commit()

        return {
            "room_type_id": room_type_id,
            "date": target_date.isoformat(),
            "occupancy_rate": occupancy,
            "forecasted_occupancy": forecast,
            "lead_time_days": lead_time,
            "saver_open": inventory.saver_open,
            "standard_open": inventory.standard_open,
            "premium_open": inventory.premium_open,
            "changes": changes,
        }

    def update_all_inventory(self, date_start: date, date_end: date) -> List[Dict]:
        """Update fare classes for all room types across a date range."""
        room_types = self.db.query(RoomType).all()
        results = []

        current = date_start
        while current <= date_end:
            for rt in room_types:
                result = self.update_fare_classes(rt.id, current)
                if result.get("changes"):
                    results.append(result)
            current += timedelta(days=1)

        return results

    def record_booking(
        self,
        room_type_id: int,
        check_in: date,
        check_out: date,
        fare_class: str,
    ) -> None:
        """Update inventory when a booking is made."""
        current = check_in
        while current < check_out:
            inventory = self.db.query(DailyInventory).filter(
                DailyInventory.room_type_id == room_type_id,
                DailyInventory.date == current,
            ).first()

            if inventory:
                inventory.booked_rooms += 1
                inventory.available_rooms = max(
                    0, inventory.total_rooms - inventory.booked_rooms - inventory.blocked_rooms
                )
                inventory.occupancy_rate = inventory.booked_rooms / max(1, inventory.total_rooms)

                # Update fare class sold count
                fc_sold_attr = f"{fare_class}_sold"
                if hasattr(inventory, fc_sold_attr):
                    setattr(inventory, fc_sold_attr, getattr(inventory, fc_sold_attr) + 1)

                # Auto-update fare class availability
                self.update_fare_classes(room_type_id, current)

            current += timedelta(days=1)

        self.db.commit()

    def block_rooms(
        self,
        room_type_id: int,
        date_start: date,
        date_end: date,
        count: int,
        reason: str = "group_block",
    ) -> Dict:
        """Block rooms for a group or event."""
        current = date_start
        blocked_dates = []
        while current <= date_end:
            inventory = self.db.query(DailyInventory).filter(
                DailyInventory.room_type_id == room_type_id,
                DailyInventory.date == current,
            ).first()

            if inventory:
                inventory.blocked_rooms += count
                inventory.available_rooms = max(
                    0, inventory.total_rooms - inventory.booked_rooms - inventory.blocked_rooms
                )
                blocked_dates.append(current.isoformat())

            current += timedelta(days=1)

        self.db.commit()
        return {
            "room_type_id": room_type_id,
            "blocked_count": count,
            "dates": blocked_dates,
            "reason": reason,
        }

    def get_inventory_summary(
        self, date_start: date, date_end: date
    ) -> List[Dict]:
        """Get inventory summary for the dashboard."""
        inventories = self.db.query(DailyInventory).filter(
            DailyInventory.date >= date_start,
            DailyInventory.date <= date_end,
        ).all()

        # Group by date
        by_date = {}
        for inv in inventories:
            d = inv.date.isoformat()
            if d not in by_date:
                by_date[d] = {
                    "date": d,
                    "total_rooms": 0,
                    "booked_rooms": 0,
                    "available_rooms": 0,
                    "occupancy_rate": 0.0,
                    "room_types": [],
                }
            by_date[d]["total_rooms"] += inv.total_rooms
            by_date[d]["booked_rooms"] += inv.booked_rooms
            by_date[d]["available_rooms"] += inv.available_rooms

            room_type = self.db.query(RoomType).get(inv.room_type_id)
            by_date[d]["room_types"].append({
                "code": room_type.code if room_type else "unknown",
                "booked": inv.booked_rooms,
                "available": inv.available_rooms,
                "occupancy": inv.occupancy_rate,
                "saver_open": inv.saver_open,
                "standard_open": inv.standard_open,
                "premium_open": inv.premium_open,
            })

        # Calculate overall occupancy
        for d in by_date.values():
            if d["total_rooms"] > 0:
                d["occupancy_rate"] = d["booked_rooms"] / d["total_rooms"]

        return list(by_date.values())
