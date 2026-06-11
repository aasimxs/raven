import phonenumbers
from phonenumbers import geocoder, carrier, timezone
import asyncio
from typing import Dict, Any

def check_phone_sync(phone: str) -> Dict[str, Any]:
    try:
        # Parse the phone number (assume it starts with + if international, otherwise default to US/Global parsing context if needed)
        # We enforce international format for OSINT checks to ensure accuracy.
        if not phone.startswith("+"):
            phone = "+" + phone
            
        parsed_number = phonenumbers.parse(phone, None)
        
        if not phonenumbers.is_valid_number(parsed_number):
            return {
                "source": "Phone OSINT",
                "exists": False,
                "error": "Invalid phone number format. Use international format (e.g. +1234567890).",
                "confidence": 0.0
            }

        # Extract intelligence
        region = geocoder.description_for_number(parsed_number, "en")
        carrier_name = carrier.name_for_number(parsed_number, "en")
        time_zones = timezone.time_zones_for_number(parsed_number)
        number_type = phonenumbers.number_type(parsed_number)
        
        # Determine line type
        type_mapping = {
            phonenumbers.PhoneNumberType.MOBILE: "Mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE: "Landline",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Landline or Mobile",
            phonenumbers.PhoneNumberType.VOIP: "VOIP/Virtual",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
            phonenumbers.PhoneNumberType.PAGER: "Pager",
            phonenumbers.PhoneNumberType.UAN: "Company/UAN",
            phonenumbers.PhoneNumberType.UNKNOWN: "Unknown"
        }
        
        line_type = type_mapping.get(number_type, "Unknown")
        
        # Build note payload for UI
        note_str = f"Region: {region} | Carrier: {carrier_name or 'Unknown'} | Type: {line_type} | Timezone: {', '.join(time_zones)}"

        return {
            "source": "Carrier Intelligence",
            "url": None, # Phone numbers don't really have a global URL
            "exists": True,
            "note": note_str,
            "confidence": 1.0
        }

    except Exception as e:
        return {
            "source": "Phone OSINT",
            "exists": False,
            "error": str(e),
            "confidence": 0.0
        }

async def run_phone_collection(phone: str) -> list:
    # Right now, we just run the carrier lookup.
    # In the future, this is where we'd add WhatsApp API checks, Truecaller checks, etc.
    results = await asyncio.gather(
        asyncio.to_thread(check_phone_sync, phone)
    )
    
    # Return all results including errors so they show up on the board
    return [r for r in results if isinstance(r, dict)]
