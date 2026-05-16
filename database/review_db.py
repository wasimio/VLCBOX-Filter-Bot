# Don't Remove Credit @vlcbox
# Subscribe YouTube Channel For Amazing Bot @vlcbox
# Ask Doubt on telegram @rickakhtar

import datetime
import motor.motor_asyncio
from info import USER_DB_URI, DATABASE_NAME

class ReviewDatabase:
    """Handles all Review & Rating related database operations."""

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        # Collection: one document per user rating
        self.ratings = self.db.user_ratings
        # Collection: pending state tracking (awaiting text review)
        self.pending = self.db.review_pending

    async def has_rated(self, user_id: int) -> bool:
        """Return True if the user has already submitted a rating."""
        doc = await self.ratings.find_one({"user_id": user_id})
        return doc is not None

    async def save_rating(self, user_id: int, username: str, stars: int) -> bool:
        """Persist the star rating for a user."""
        if await self.has_rated(user_id):
            return False
        doc = {
            "user_id": user_id,
            "username": username or "Unknown",
            "stars": stars,
            "review_text": None,
            "rated_at": datetime.datetime.utcnow(),
            "reviewed_at": None,
        }
        await self.ratings.insert_one(doc)
        return True

    async def save_review_text(self, user_id: int, text: str) -> bool:
        """Attach a written review to an existing rating."""
        result = await self.ratings.update_one(
            {"user_id": user_id, "review_text": None},
            {
                "$set": {
                    "review_text": text,
                    "reviewed_at": datetime.datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def get_rating(self, user_id: int) -> dict:
        """Return the full rating document for a user."""
        return await self.ratings.find_one({"user_id": user_id})

    async def set_pending(self, user_id: int, stars: int):
        """Mark a user as awaiting their text review after rating."""
        await self.pending.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "stars": stars,
                    "created_at": datetime.datetime.utcnow(),
                }
            },
            upsert=True,
        )

    async def get_pending(self, user_id: int) -> dict:
        """Return pending state for user."""
        return await self.pending.find_one({"user_id": user_id})

    async def clear_pending(self, user_id: int):
        """Remove the pending review state for a user."""
        await self.pending.delete_many({"user_id": user_id})

    async def total_ratings_count(self) -> int:
        return await self.ratings.count_documents({})

    async def distribution(self) -> dict:
        """Return {1: count, 2: count, ..., 5: count}."""
        pipeline = [
            {"$group": {"_id": "$stars", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        dist = {i: 0 for i in range(1, 6)}
        async for doc in self.ratings.aggregate(pipeline):
            dist[doc["_id"]] = doc["count"]
        return dist

    async def average_rating(self) -> float:
        """Return the average star rating."""
        pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$stars"}}}]
        async for doc in self.ratings.aggregate(pipeline):
            return round(doc["avg"], 2)
        return 0.0

    async def latest_reviews(self, limit: int = 5) -> list:
        """Return the most recent reviews that have text."""
        cursor = (
            self.ratings.find({"review_text": {"$ne": None}})
            .sort("reviewed_at", -1)
            .limit(limit)
        )
        return [doc async for doc in cursor]

review_db = ReviewDatabase(USER_DB_URI, DATABASE_NAME)
