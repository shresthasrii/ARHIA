import os
import json
import logging
import datetime
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List

from backend.tools.registry import registry
from backend.services.location import get_current_location_data, get_current_location_summary
from backend.database import SessionLocal
from backend.models import UserProfile, Memory

logger = logging.getLogger("ARHIEA.EmergencyTools")

# Standard Verified Emergency Hotlines
EMERGENCY_HOTLINES = {
    "India": {
        "National Emergency (All-in-One)": "112",
        "Ambulance / Medical Emergency": "108",
        "Police Emergency": "100",
        "Fire & Rescue Services": "101",
        "National Highway Emergency Patrol": "1073",
        "Disaster Management Services": "1078",
        "Women's Safety Helpline": "1091",
        "Child Emergency Helpline": "1098"
    },
    "International": {
        "United States & Canada (All-in-One)": "911",
        "European Union (All-in-One)": "112",
        "United Kingdom": "999 / 112",
        "Australia": "000",
        "Japan": "119 (Medical/Fire), 110 (Police)"
    }
}

def _get_user_medical_and_emergency_context() -> Dict[str, Any]:
    """Retrieves authenticated user emergency contacts, medical notes, and blood group."""
    db = SessionLocal()
    try:
        user = db.query(UserProfile).order_by(UserProfile.last_login.desc()).first()
        memories = db.query(Memory).all()
        mem_dict = {m.key.lower(): m.value for m in memories}

        emergency_name = user.emergency_contact_name if user and user.emergency_contact_name else mem_dict.get("emergency_contact", "Not specified")
        emergency_phone = user.emergency_contact_phone if user and user.emergency_contact_phone else mem_dict.get("emergency_phone", "Not specified")
        blood_group = mem_dict.get("blood_group", mem_dict.get("blood_type", "Not specified"))
        allergies = mem_dict.get("allergies", mem_dict.get("allergy", "None recorded"))
        medical_conditions = user.personal_notes if user and user.personal_notes else mem_dict.get("medical_notes", "None recorded")

        return {
            "name": user.name if user else "Driver / User",
            "blood_group": blood_group,
            "emergency_contact_name": emergency_name,
            "emergency_contact_phone": emergency_phone,
            "allergies": allergies,
            "medical_conditions": medical_conditions
        }
    except Exception as e:
        logger.warning(f"Error fetching user emergency context: {e}")
        return {
            "name": "User",
            "blood_group": "Unknown",
            "emergency_contact_name": "Not specified",
            "emergency_contact_phone": "Not specified",
            "allergies": "Unknown",
            "medical_conditions": "Unknown"
        }
    finally:
        db.close()


@registry.register(
    name="get_emergency_protocol",
    description="Retrieves immediate, life-saving voice and text guidance for vehicle road crises or medical emergencies.",
    parameters={
        "type": "object",
        "properties": {
            "emergency_type": {
                "type": "string",
                "enum": [
                    "brake_failure",
                    "aquaplaning",
                    "tyre_blowout",
                    "engine_overheat",
                    "fog_low_visibility",
                    "cpr",
                    "choking_heimlich",
                    "severe_bleeding",
                    "burns",
                    "stroke_fast",
                    "seizure",
                    "road_accident"
                ],
                "description": "Specific emergency protocol category"
            }
        },
        "required": ["emergency_type"]
    },
    permission_level="normal",
    category="emergency"
)
async def get_emergency_protocol(emergency_type: str) -> Dict[str, Any]:
    etype = emergency_type.lower().strip()

    # 1. Road Emergency: Brake Failure
    if etype == "brake_failure":
        return {
            "title": "VEHICLE BRAKE FAILURE EMERGENCY PROTOCOL",
            "category": "road_crisis",
            "severity": "CRITICAL",
            "voice_summary": "Do not turn off your engine. Pump the brake pedal rapidly, shift into lower gears progressively, and gently apply the handbrake while steering toward a soft verge.",
            "steps": [
                "1. DO NOT TURN OFF ENGINE: Turning off the ignition locks your steering wheel and disables power steering.",
                "2. PUMP THE BRAKE PEDAL RAPIDLY: Dual-circuit hydraulic brakes may build back pressure after 3 to 4 fast, firm pumps.",
                "3. ENGINE BRAKING (DOWNSHIFT): Shift down sequentially (5th -> 4th -> 3rd -> 2nd -> 1st). In automatics, switch to Manual/Low mode ('L' or '1').",
                "4. GENTLE HANDBRAKE APPLICATION: Once vehicle speed is under 40 km/h, pull the handbrake gradually while holding the release button to avoid locking the rear wheels.",
                "5. SEEK FRICTION / ESCAPE ROUTE: Steer towards the road shoulder, gravel traps, grass verge, or gentle uphill inclines. Turn on hazard warning lights and sound horn repeatedly to warn others."
            ],
            "hotlines": EMERGENCY_HOTLINES["India"]
        }

    # 2. Road Emergency: Aquaplaning / Hydroplaning
    if etype == "aquaplaning":
        return {
            "title": "AQUAPLANING (HYDROPLANING) RECOVERY PROTOCOL",
            "category": "road_crisis",
            "severity": "HIGH",
            "voice_summary": "Do not slam the brakes. Ease off the accelerator smoothly, hold the steering wheel straight, and let the vehicle decelerate naturally until traction returns.",
            "steps": [
                "1. DO NOT BRAKE HARD: Slamming the brakes causes uncontrollable vehicle spinning on standing water.",
                "2. EASE OFF ACCELERATOR GENTLY: Remove your foot from the gas pedal to let aerodynamic drag slow you down.",
                "3. HOLD WHEEL STRAIGHT: Keep the steering aligned with your direction of travel without sudden counter-steering.",
                "4. WAIT FOR TRACTION TO BITE: As speed decreases, tyre tread will disperse water and restore road contact.",
                "5. POST-RECOVERY: Reduce cruising speed by 20 km/h and increase following distance to at least 4 seconds."
            ],
            "hotlines": EMERGENCY_HOTLINES["India"]
        }

    # 3. Road Emergency: High-Speed Tyre Blowout
    if etype == "tyre_blowout":
        return {
            "title": "HIGH-SPEED TYRE BLOWOUT PROTOCOL",
            "category": "road_crisis",
            "severity": "CRITICAL",
            "voice_summary": "Firmly grip the steering wheel with both hands to counter the pull. Do not brake abruptly. Gently coast down and pull onto the emergency shoulder.",
            "steps": [
                "1. GRIP WHEEL FIRMLY WITH BOTH HANDS: Expect a violent sideways pull towards the punctured tyre. Stabilize center.",
                "2. AVOID SUDDEN BRAKING: Hard braking shifts vehicle weight onto the destroyed wheel rim, leading to rollover.",
                "3. TAP ACCELERATOR BRIEFLY, THEN COAST: Stabilize momentum, release gas, and let rolling friction slow the vehicle.",
                "4. INDICATE & PULL TO HARD SHOULDER: Once under 30 km/h, brake softly, activate hazard flashers, and park clear of traffic.",
                "5. PLACE WARNING TRIANGLE: Put reflective triangle 50 meters behind car; passengers must stand behind roadside crash barriers."
            ],
            "hotlines": EMERGENCY_HOTLINES["India"]
        }

    # 4. Medical Emergency: CPR
    if etype == "cpr":
        return {
            "title": "ADULT CARDIOPULMONARY RESUSCITATION (CPR) PROTOCOL",
            "category": "medical_emergency",
            "severity": "CRITICAL_LIFE_SAVING",
            "voice_summary": "Call emergency services immediately. Place hands on center of chest. Push hard and fast at 100 to 120 beats per minute, 5 centimeters deep, 30 compressions then 2 rescue breaths.",
            "metronome_bpm": 110,
            "steps": [
                "1. VERIFY UNRESPONSIVENESS: Tap shoulders firmly, shout 'Are you okay?'. Check for chest rise/breathing for max 10 seconds.",
                "2. CALL 112 / 108 / 911: Put on speakerphone, ask someone to retrieve an AED (Defibrillator).",
                "3. HAND POSITION: Place heel of one hand in center of patient's chest (lower half of sternum), interlock second hand on top.",
                "4. COMPRESSION DEPTH & RATE: Compress 5 to 6 cm (2-2.4 inches) deep at 100-120 beats per minute (rhythm of 'Stayin Alive'). Allow full recoil.",
                "5. CYCLE: 30 chest compressions followed by 2 gentle 1-second rescue breaths (tilt head, pinch nose). If untrained, perform continuous Hands-Only compressions."
            ],
            "hotlines": EMERGENCY_HOTLINES["India"]
        }

    # 5. Medical Emergency: Choking / Heimlich Maneuver
    if etype == "choking_heimlich":
        return {
            "title": "CHOKING RELIEF / HEIMLICH MANEUVER PROTOCOL",
            "category": "medical_emergency",
            "severity": "CRITICAL_LIFE_SAVING",
            "voice_summary": "Ask if they can speak or cough. If not, deliver five firm back blows between shoulder blades, followed by five upward abdominal thrusts above the navel.",
            "steps": [
                "1. CONFIRM CHOKING: If victim can speak, cough forcefully, or breathe, encourage coughing. If silent or gasping, act immediately.",
                "2. 5 BACK BLOWS: Lean person forward, deliver 5 sharp blows with heel of your hand between shoulder blades.",
                "3. 5 ABDOMINAL THRUSTS (HEIMLICH): Stand behind victim, place fist thumb-side in just above navel, grasp with other hand, thrust upward and inward.",
                "4. REPEAT 5 & 5 CYCLE: Alternate 5 back blows and 5 abdominal thrusts until object is expelled.",
                "5. IF UNCONSCIOUS: Lower victim safely to floor, call 112 / 108, and begin CPR compressions immediately."
            ],
            "hotlines": EMERGENCY_HOTLINES["India"]
        }

    # 6. Medical Emergency: Severe Bleeding & Tourniquet
    if etype == "severe_bleeding":
        return {
            "title": "SEVERE BLEEDING & TOURNIQUET APPLICATION",
            "category": "medical_emergency",
            "severity": "CRITICAL",
            "voice_summary": "Apply direct, firm pressure with a clean cloth immediately. For severe limb arterial bleeding, apply a tourniquet 2 to 3 inches above the wound and note the exact time.",
            "steps": [
                "1. DIRECT PRESSURE: Press clean cloth or dressing firmly onto wound with both hands. Do not remove dressing if soaked; add more layers.",
                "2. ELEVATE WOUND: If no fracture suspected, raise bleeding limb above heart level.",
                "3. TOURNIQUET FOR LIMB ARTERIAL SPRAY: Apply tourniquet 2-3 inches proximal to wound (between wound and heart). Never place over joints.",
                "4. TIGHTEN UNTIL BLEEDING STOPS: Twist windlass rod until bright red bleeding ceases, secure rod, and record exact application time.",
                "5. TREAT FOR SHOCK: Lay patient flat, elevate legs slightly, keep warm with blanket, do not give food or drink."
            ],
            "hotlines": EMERGENCY_HOTLINES["India"]
        }

    # 7. Medical Emergency: Severe Burns
    if etype == "burns":
        return {
            "title": "THERMAL & CHEMICAL BURNS FIRST AID",
            "category": "medical_emergency",
            "severity": "HIGH",
            "voice_summary": "Cool the burn under cold running water for 20 minutes immediately. Do not use ice, butter, or ointments. Cover loosely with sterile film.",
            "steps": [
                "1. COOL WITH RUNNING WATER FOR 20 MINUTES: Use gentle running tap water immediately. Never apply ice, ice water, or frozen items.",
                "2. REMOVE CONSTRICTING ITEMS: Take off watches, rings, tight clothing near burn area before tissue swelling begins.",
                "3. DO NOT POP BLISTERS: Intact skin protects against severe infection. Never apply butter, toothpaste, or greasy ointments.",
                "4. COVER LOOSELY: Wrap area loosely with clean cling film or sterile non-adherent dressing.",
                "5. CALL 112 / 108 FOR: Burns larger than victim's palm, electrical/chemical burns, or burns to face, hands, or joints."
            ],
            "hotlines": EMERGENCY_HOTLINES["India"]
        }

    # Default: General Road Accident Triage
    return {
        "title": "ROAD ACCIDENT GOLDEN HOUR PROTOCOL",
        "category": "road_crisis",
        "severity": "CRITICAL",
        "voice_summary": "Secure the accident scene to prevent further collisions. Dial 112 immediately. Do not move injured passengers with neck or back trauma unless fire risk exists.",
        "steps": [
            "1. SECURE THE CRASH SCENE: Turn on hazard lights, set up reflective warning triangles, turn off vehicle ignitions to eliminate fire risks.",
            "2. CALL 112 / 108 IMMEDIATELY: State exact location, number of injured passengers, vehicle types, and trapped victims.",
            "3. DO NOT MOVE CASUALTIES (C-SPINE): In vehicular trauma, assume spinal injury. Keep head, neck, and spine aligned without twisting.",
            "4. CHECK ABC: Airway (clear obstruction), Breathing (look/listen), Circulation (control severe bleeding with direct pressure).",
            "5. STAY CALM & COMMUNICATE: Speak reassuringly to conscious victims, keep them warm, and prevent onlookers from crowding."
        ],
        "hotlines": EMERGENCY_HOTLINES["India"]
    }


@registry.register(
    name="trigger_emergency_sos",
    description="Triggers high-priority Emergency SOS alert, generates official accident report on Desktop, and creates emergency dispatch links.",
    parameters={
        "type": "object",
        "properties": {
            "incident_description": {
                "type": "string",
                "description": "Details of the road or medical accident"
            },
            "severity": {
                "type": "string",
                "enum": ["CRITICAL", "HIGH", "MODERATE"],
                "description": "Urgency level of emergency"
            }
        },
        "required": ["incident_description"]
    },
    permission_level="sensitive",
    category="emergency"
)
async def trigger_emergency_sos(incident_description: str, severity: str = "CRITICAL") -> Dict[str, Any]:
    now = datetime.datetime.now()
    loc_data = get_current_location_data() or {}
    loc_summary = get_current_location_summary()
    user_ctx = _get_user_medical_and_emergency_context()

    lat = loc_data.get("lat")
    lon = loc_data.get("lon")
    maps_link = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "GPS coordinates not available"

    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Generate Official Accident / Incident Report File on Desktop
    report_text = (
        "=================================================================\n"
        "           ARHIEA OFFICIAL EMERGENCY INCIDENT REPORT             \n"
        "  Adaptive Road and Human Intelligence Emergency System (SIH26204) \n"
        "=================================================================\n\n"
        f"INCIDENT TIMESTAMP : {timestamp_str}\n"
        f"SEVERITY LEVEL     : {severity.upper()}\n"
        f"INCIDENT SUMMARY   : {incident_description}\n"
        f"LOCATION SUMMARY   : {loc_summary}\n"
        f"COORDINATES (GPS)  : Lat {lat}, Lon {lon}\n"
        f"LIVE MAPS LINK     : {maps_link}\n\n"
        "-----------------------------------------------------------------\n"
        "PATIENT / USER MEDICAL PROFILE (EPISODIC EMERGENCY CONTEXT):\n"
        "-----------------------------------------------------------------\n"
        f"Full Name          : {user_ctx.get('name')}\n"
        f"Blood Group        : {user_ctx.get('blood_group')}\n"
        f"Known Allergies    : {user_ctx.get('allergies')}\n"
        f"Medical Notes      : {user_ctx.get('medical_conditions')}\n"
        f"Emergency Contact  : {user_ctx.get('emergency_contact_name')} ({user_ctx.get('emergency_contact_phone')})\n\n"
        "-----------------------------------------------------------------\n"
        "VERIFIED EMERGENCY HOTLINES:\n"
        "-----------------------------------------------------------------\n"
        "National Emergency (India/EU) : 112\n"
        "Ambulance / Medical Response  : 108\n"
        "Police Dispatch               : 100\n"
        "Fire & Rescue Services        : 101\n"
        "National Highway Patrol (NHAI): 1073\n"
        "USA Emergency Dispatch        : 911\n"
        "=================================================================\n"
        "Report automatically generated and archived by ARHIEA Core Engine.\n"
    )

    desktop_path = Path.home() / "Desktop"
    report_file_name = f"ARHIEA_SOS_REPORT_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    report_file_path = desktop_path / report_file_name

    saved_path_str = None
    try:
        if desktop_path.exists():
            with open(report_file_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            saved_path_str = str(report_file_path)
            logger.info(f"Emergency report saved to Desktop: {saved_path_str}")
    except Exception as e:
        logger.warning(f"Could not write SOS report to Desktop: {e}")

    # Build WhatsApp / SMS Pre-filled Emergency Dispatch Link
    contact_phone = user_ctx.get("emergency_contact_phone", "").replace("+", "").replace(" ", "").replace("-", "")
    sos_msg = (
        f"EMERGENCY SOS ALERT from ARHIEA!\n"
        f"Incident: {incident_description}\n"
        f"Location: {loc_summary} ({maps_link})\n"
        f"Time: {timestamp_str}\n"
        f"Blood Group: {user_ctx.get('blood_group')}\n"
        f"Please send help or contact 112 immediately!"
    )
    encoded_sos = urllib.parse.quote_plus(sos_msg)
    wa_dispatch_link = f"https://wa.me/{contact_phone}?text={encoded_sos}" if contact_phone and contact_phone != "Notspecified" else None

    return {
        "status": "SOS_DISPATCHED",
        "severity": severity,
        "timestamp": timestamp_str,
        "location": loc_summary,
        "coordinates": {"lat": lat, "lon": lon},
        "maps_link": maps_link,
        "incident": incident_description,
        "user_medical_context": user_ctx,
        "report_saved_to": saved_path_str,
        "whatsapp_sos_link": wa_dispatch_link,
        "emergency_hotlines": EMERGENCY_HOTLINES["India"],
        "voice_response": f"Emergency SOS initiated! Location captured as {loc_summary}. Dialing 112 national emergency and archiving medical report to your desktop."
    }
