from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging
from context import AirlineAgentContext
from database import db_client
from agents import function_tool

logger = logging.getLogger(__name__)

@function_tool(
    name_override="get_conference_sessions",
    description_override="Fetch conference sessions with filtering."
)
async def get_conference_sessions(
    speaker_name: Optional[str] = None,
    topic: Optional[str] = None,
    conference_room_name: Optional[str] = None,
    track_name: Optional[str] = None,
    conference_date: Optional[date] = None,
    time_range_start: Optional[datetime] = None,
    time_range_end: Optional[datetime] = None,
    limit: Optional[int] = None,
    context: Optional[AirlineAgentContext] = None
) -> str:
    """Fetch conference sessions with filtering."""
    try:
        filters = {}
        if speaker_name:
            filters["speaker_name"] = speaker_name
        if topic:
            filters["topic"] = topic
        if conference_room_name:
            filters["conference_room_name"] = conference_room_name
        if track_name:
            filters["track_name"] = track_name
        if conference_date:
            filters["conference_date"] = conference_date.isoformat()
        if time_range_start:
            filters["start_time"] = time_range_start.isoformat()
        if time_range_end:
            filters["end_time"] = time_range_end.isoformat()
        
        sessions = await db_client.query(
            table_name="conference_schedules",
            filters=filters,
            order_by=[{"column": "conference_date"}, {"column": "start_time"}],
            limit=limit
        )
        
        if not sessions:
            logger.warning("❌ No conference sessions found")
            return "No conference sessions found matching the criteria."
        
        result = f"Found {len(sessions)} conference sessions:\n"
        for i, session in enumerate(sessions[:3], 1):
            result += (
                f"{i}. {session.get('topic')} by {session.get('speaker_name')} "
                f"on {session.get('conference_date')} at {session.get('start_time')}\n"
            )
        if len(sessions) > 3:
            result += f"...and {len(sessions) - 3} more."
        
        logger.info(f"✅ Found {len(sessions)} conference sessions")
        return result
    except Exception as e:
        logger.error(f"❌ Error fetching conference sessions: {e}", exc_info=True)
        return f"Error fetching conference sessions: {str(e)}"

@function_tool(
    name_override="get_all_speakers",
    description_override="Get all unique speakers."
)
async def get_all_speakers(context: AirlineAgentContext) -> str:
    """Get all unique speakers."""
    try:
        speakers = await db_client.query(
            table_name="conference_schedules",
            select_fields="speaker_name"
        )
        if not speakers:
            logger.warning("❌ No speakers found")
            return "No speakers found."
        
        unique_speakers = sorted(set(item["speaker_name"] for item in speakers if item.get("speaker_name")))
        logger.info(f"✅ Found {len(unique_speakers)} unique speakers")
        return f"Available speakers: {', '.join(unique_speakers)}"
    except Exception as e:
        logger.error(f"❌ Error fetching speakers: {e}", exc_info=True)
        return f"Error fetching speakers: {str(e)}"

@function_tool(
    name_override="get_all_tracks",
    description_override="Get all unique tracks."
)
async def get_all_tracks(context: AirlineAgentContext) -> str:
    """Get all unique tracks."""
    try:
        tracks = await db_client.query(
            table_name="conference_schedules",
            select_fields="track_name"
        )
        if not tracks:
            logger.warning("❌ No tracks found")
            return "No tracks found."
        
        unique_tracks = sorted(set(item["track_name"] for item in tracks if item.get("track_name")))
        logger.info(f"✅ Found {len(unique_tracks)} unique tracks")
        return f"Available tracks: {', '.join(unique_tracks)}"
    except Exception as e:
        logger.error(f"❌ Error fetching tracks: {e}", exc_info=True)
        return f"Error fetching tracks: {str(e)}"

@function_tool(
    name_override="get_all_rooms",
    description_override="Get all unique rooms."
)
async def get_all_rooms(context: AirlineAgentContext) -> str:
    """Get all unique rooms."""
    try:
        rooms = await db_client.query(
            table_name="conference_schedules",
            select_fields="conference_room_name"
        )
        if not rooms:
            logger.warning("❌ No rooms found")
            return "No rooms found."
        
        unique_rooms = sorted(set(item["conference_room_name"] for item in rooms if item.get("conference_room_name")))
        logger.info(f"✅ Found {len(unique_rooms)} unique rooms")
        return f"Available rooms: {', '.join(unique_rooms)}"
    except Exception as e:
        logger.error(f"❌ Error fetching rooms: {e}", exc_info=True)
        return f"Error fetching rooms: {str(e)}"