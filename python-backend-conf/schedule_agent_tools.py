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
    conference_date: Optional[str] = None,
    limit: Optional[int] = 10,
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
            filters["conference_date"] = conference_date
        
        # Use synchronous query since Supabase Python client is sync
        sessions = db_client.query(
            table_name="conference_schedules",
            filters=filters,
            order_by=[{"column": "conference_date"}, {"column": "start_time"}],
            limit=limit
        )
        
        if not sessions:
            logger.warning("❌ No conference sessions found")
            return "No conference sessions found matching the criteria."
        
        result = f"**Aviation Tech Summit 2025 Sessions** ({len(sessions)} found):\n\n"
        for i, session in enumerate(sessions[:5], 1):
            result += (
                f"**{i}. {session.get('topic', 'TBA')}**\n"
                f"   👤 Speaker: {session.get('speaker_name', 'TBA')}\n"
                f"   📅 Date: {session.get('conference_date', 'TBA')}\n"
                f"   🕐 Time: {session.get('start_time', 'TBA')}\n"
                f"   📍 Room: {session.get('conference_room_name', 'TBA')}\n"
                f"   🏷️ Track: {session.get('track_name', 'TBA')}\n\n"
            )
        if len(sessions) > 5:
            result += f"...and {len(sessions) - 5} more sessions available."
        
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
        speakers = db_client.query(
            table_name="conference_schedules",
            select_fields="speaker_name"
        )
        if not speakers:
            logger.warning("❌ No speakers found")
            return "No speakers found in the conference database."
        
        unique_speakers = sorted(set(item["speaker_name"] for item in speakers if item.get("speaker_name")))
        logger.info(f"✅ Found {len(unique_speakers)} unique speakers")
        
        result = f"**Aviation Tech Summit 2025 Speakers** ({len(unique_speakers)} total):\n\n"
        for i, speaker in enumerate(unique_speakers, 1):
            result += f"{i}. {speaker}\n"
        
        return result
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
        tracks = db_client.query(
            table_name="conference_schedules",
            select_fields="track_name"
        )
        if not tracks:
            logger.warning("❌ No tracks found")
            return "No tracks found in the conference database."
        
        unique_tracks = sorted(set(item["track_name"] for item in tracks if item.get("track_name")))
        logger.info(f"✅ Found {len(unique_tracks)} unique tracks")
        
        result = f"**Aviation Tech Summit 2025 Tracks** ({len(unique_tracks)} total):\n\n"
        for i, track in enumerate(unique_tracks, 1):
            result += f"{i}. {track}\n"
        
        return result
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
        rooms = db_client.query(
            table_name="conference_schedules",
            select_fields="conference_room_name"
        )
        if not rooms:
            logger.warning("❌ No rooms found")
            return "No rooms found in the conference database."
        
        unique_rooms = sorted(set(item["conference_room_name"] for item in rooms if item.get("conference_room_name")))
        logger.info(f"✅ Found {len(unique_rooms)} unique rooms")
        
        result = f"**Aviation Tech Summit 2025 Rooms** ({len(unique_rooms)} total):\n\n"
        for i, room in enumerate(unique_rooms, 1):
            result += f"{i}. {room}\n"
        
        return result
    except Exception as e:
        logger.error(f"❌ Error fetching rooms: {e}", exc_info=True)
        return f"Error fetching rooms: {str(e)}"