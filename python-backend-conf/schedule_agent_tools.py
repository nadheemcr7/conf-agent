from typing import Optional
import logging
from context import AirlineAgentContext
from database import db_client
from agents import function_tool

logger = logging.getLogger(__name__)

@function_tool(
    name_override="get_conference_sessions",
    description_override="Get conference sessions"
)
def get_conference_sessions(context: AirlineAgentContext) -> str:
    """Fetch conference sessions."""
    try:
        # Use synchronous query - remove await
        sessions = db_client.table("conference_schedules").select("*").limit(5).execute()
        
        if not sessions.data:
            return "No conference sessions found."
        
        result = f"**Aviation Tech Summit 2025 Sessions** ({len(sessions.data)} found):\n\n"
        for i, session in enumerate(sessions.data, 1):
            result += (
                f"**{i}. {session.get('topic', 'TBA')}**\n"
                f"   👤 Speaker: {session.get('speaker_name', 'TBA')}\n"
                f"   📅 Date: {session.get('conference_date', 'TBA')}\n"
                f"   🕐 Time: {session.get('start_time', 'TBA')}\n"
                f"   📍 Room: {session.get('conference_room_name', 'TBA')}\n\n"
            )
        
        logger.info(f"✅ Found {len(sessions.data)} conference sessions")
        return result
    except Exception as e:
        logger.error(f"❌ Error fetching conference sessions: {e}", exc_info=True)
        return "Error fetching conference sessions. Please try again."

@function_tool(
    name_override="get_all_speakers",
    description_override="Get all speakers"
)
def get_all_speakers(context: AirlineAgentContext) -> str:
    """Get all unique speakers."""
    try:
        speakers = db_client.table("conference_schedules").select("speaker_name").execute()
        
        if not speakers.data:
            return "No speakers found."
        
        unique_speakers = sorted(set(item["speaker_name"] for item in speakers.data if item.get("speaker_name")))
        
        result = f"**Aviation Tech Summit 2025 Speakers** ({len(unique_speakers)} total):\n\n"
        for i, speaker in enumerate(unique_speakers[:10], 1):
            result += f"{i}. {speaker}\n"
        
        if len(unique_speakers) > 10:
            result += f"\n...and {len(unique_speakers) - 10} more speakers."
        
        return result
    except Exception as e:
        logger.error(f"❌ Error fetching speakers: {e}", exc_info=True)
        return "Error fetching speakers. Please try again."

@function_tool(
    name_override="get_all_tracks",
    description_override="Get all tracks"
)
def get_all_tracks(context: AirlineAgentContext) -> str:
    """Get all unique tracks."""
    try:
        tracks = db_client.table("conference_schedules").select("track_name").execute()
        
        if not tracks.data:
            return "No tracks found."
        
        unique_tracks = sorted(set(item["track_name"] for item in tracks.data if item.get("track_name")))
        
        result = f"**Aviation Tech Summit 2025 Tracks** ({len(unique_tracks)} total):\n\n"
        for i, track in enumerate(unique_tracks, 1):
            result += f"{i}. {track}\n"
        
        return result
    except Exception as e:
        logger.error(f"❌ Error fetching tracks: {e}", exc_info=True)
        return "Error fetching tracks. Please try again."

@function_tool(
    name_override="get_all_rooms",
    description_override="Get all rooms"
)
def get_all_rooms(context: AirlineAgentContext) -> str:
    """Get all unique rooms."""
    try:
        rooms = db_client.table("conference_schedules").select("conference_room_name").execute()
        
        if not rooms.data:
            return "No rooms found."
        
        unique_rooms = sorted(set(item["conference_room_name"] for item in rooms.data if item.get("conference_room_name")))
        
        result = f"**Aviation Tech Summit 2025 Rooms** ({len(unique_rooms)} total):\n\n"
        for i, room in enumerate(unique_rooms, 1):
            result += f"{i}. {room}\n"
        
        return result
    except Exception as e:
        logger.error(f"❌ Error fetching rooms: {e}", exc_info=True)
        return "Error fetching rooms. Please try again."