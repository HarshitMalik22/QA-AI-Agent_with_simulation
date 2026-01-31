import os
import json
import logging
import requests
import asyncio
from typing import Dict, Any, Optional
from telegram import Update, Bot, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from deepgram import DeepgramClient

# Reuse existing modules
from modules.llm_service import LLMService
from modules.assistant_tools import (
    TOOLS_SCHEMA,
    get_driver_profile,
    get_swap_history,
    get_nearest_station,
    get_nearest_dsk,
    get_plan_details,
    verify_driver_by_id,
    report_issue,
    check_penalty_status,
    escalate_to_agent
)
from modules.simulation import driver_sim

logger = logging.getLogger(__name__)

class TelegramHandler:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.deepgram_key = os.environ.get("DEEPGRAM_API_KEY")
        self.llm_service = LLMService()
        
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not set. Telegram features disabled.")
            self.bot = None
        else:
            self.bot = Bot(token=self.token)
            
        if not self.deepgram_key:
            logger.error("DEEPGRAM_API_KEY not set. Voice features disabled.")
            self.deepgram = None
        else:
            self.deepgram = DeepgramClient(api_key=self.deepgram_key)
            
        # Context system prompt for Raju
        self.system_prompt = """
        You are **Raju Rastogi**, a helpful Support Agent for 'Battery Smart'.
        
        **CRITICAL SECURITY PROTOCOL (FOLLOW ALWAYS):**
        1. **MANDATORY ID CHECK**: If the user asks for sensitive info (balance, plan, swaps, payment), you **MUST** ask for their **Driver ID** first.
        2. **NO ASSUMPTIONS**: Do NOT provide any account details just because you have the phone number. **Driver ID is mandatory.**
        3. **IF NO ID PROVIDED**: Reply "Kripya suraksha ke liye apna Driver ID (e.g. D12...) batayein."
        4. **ONLY AFTER ID IS GIVEN**: Call `verify_driver_by_id(driver_id="...")`.
           - If verified: "Dhanyawaad [NAME] ji. Verify ho gaya." -> THEN answer the query.
           - If invalid: "Ye ID system mein nahi mili. Kripya sahi ID batayein."

        **LANGUAGE SELECTION:**
        - **FIRST GREETING**: If the user says "Hi", "Hello", "/start" or starts a new conversation:
          - **SAY**: "Namaste Sir! Main Raju, Battery Smart se. Aap kis bhaasha mein baat karna chahenge: Hindi, English, Bangla, ya Marathi?"
        - **ADAPT**: 
          - **English**: Respond in English.
          - **Hindi**: Respond in Hindi (Devanagari).
          - **Bangla**: Respond in Bengali.
          - **Marathi**: Respond in Marathi.
          - Maintain this language.

        **PRICING STRUCTURE (AUTHORITATIVE):**
        - **Components**: Swap Price + Leave Penalty + Service Charge.
        - **Base Swap Price**: ₹170 (First swap of the day).
        - **Secondary Swap Price**: ₹70 (Subsequent swaps).
        - **Service Charge**: ₹40 per swap (Added to EVERY swap).
        - **Leave Penalty**: 
          - 4 leave days/month FREE.
          - Beyond 4 days: ₹120 penalty applied.
          - Recovery: ₹60 deducted per swap until paid.

        **ESCALATION LOGIC (CRITICAL):**
        1. **CUSTOMER DISSATISFACTION / ARGUING / ANGRY**
           - If the user argues about ANYTHING, sounds angry, or if the conversation is going in circles.
           - **ACTION**: Call `escalate_to_agent(reason="User Dissatisfied/Arguing")` IMMEDIATELY.
           - **SAY**: "Sir, main samajh sakta hoon ki aap santusht nahi hain. Main apki baat apne senior team se karvata hoon."

        2. **"गाड़ी खराब" / "issue" = REPORT ISSUE**
           - If driver reports technical issue: Call `report_issue`.

        **Tone**: Polite, Desi, Helpful.
        **Response Length**: Keep responses short (under 50 words) for chat.
        """
        self.sessions = {}

    async def process_update(self, update_data: Dict[str, Any]):
        """
        Manually process a webhook update from Telegram.
        """
        if not self.bot:
            return {"error": "Bot not configured"}

        try:
            update = Update.de_json(update_data, self.bot)
            
            if not update.message:
                return {"status": "ignored", "reason": "no message"}

            chat_id = update.message.chat_id
            user_text = ""
            
            # Handle Voice
            if update.message.voice:
                file_id = update.message.voice.file_id
                user_text = await self._transcribe_voice(file_id)
                if not user_text:
                    await self.bot.send_message(chat_id=chat_id, text="माफ़ कीजिए सर, आवाज़ साफ़ नहीं आई। कृपया लिखकर भेजें।")
                    return {"status": "error", "reason": "transcription failed"}

            # Handle Photo
            elif update.message.photo:
                # Use the largest photo available
                photo = update.message.photo[-1]
                file_id = photo.file_id
                
                # Get File URL
                new_file = await self.bot.get_file(file_id)
                file_url = new_file.file_path
                
                # Send to Vision Model
                analysis = self.llm_service.analyze_image(file_url, "User sent this image. Analyze it in context of battery swapping or vehicle issues. Reply directly to user in Hindi.")
                
                await self.bot.send_message(chat_id=chat_id, text=analysis)
                return {"status": "success", "type": "vision", "response": analysis}

            # Handle Location
            elif update.message.location:
                lat = update.message.location.latitude
                lon = update.message.location.longitude
                
                # Call get_nearest_station directly with coordinates
                result = get_nearest_station(lat=lat, lon=lon)
                
                if "stations" in result and result["stations"]:
                    stn = result["stations"][0]
                    # Send response
                    await self.bot.send_message(
                        chat_id=chat_id, 
                        text=f"नमस्ते सर! आपके पास सबसे नज़दीक स्टेशन है:\n\n📍 **{stn['name']}**\nदूरी: {stn['distance_km']} km"
                    )
                    # Send pin
                    await self.bot.send_location(chat_id=chat_id, latitude=stn['location']['lat'], longitude=stn['location']['lon'])
                    return {"status": "success", "type": "location", "station": stn['name']}
                else:
                    await self.bot.send_message(chat_id=chat_id, text="माफ़ कीजिए सर, आपके आस-पास कोई स्टेशन नहीं मिला।")
                    return {"status": "error", "reason": "no station found"}
                    
            # Handle Text
            elif update.message.text:
                user_text = update.message.text
                
            else:
                await self.bot.send_message(chat_id=chat_id, text="नमस्ते सर! कृपया फोटो, ऑडियो, लोकेशन या टेक्स्ट भेजें।")
                return {"status": "ignored", "reason": "unsupported content"}

            # Generate Response (let LLM handle conversation naturally)
            response_text = await self._generate_response(user_text, chat_id)
            
            logger.info(f"Bot Response: {response_text}")

            # Send Reply
            await self.bot.send_message(chat_id=chat_id, text=response_text, reply_markup=ReplyKeyboardRemove())
            
            return {
                "status": "success", 
                "user": user_text, 
                "bot": response_text
            }

        except Exception as e:
            logger.error(f"Telegram Error: {e}")
            return {"error": str(e)}

    async def _transcribe_voice(self, file_id: str) -> str:
        """
        Download voice note from Telegram and transcribe using Deepgram.
        """
        try:
            # 1. Get File URL
            new_file = await self.bot.get_file(file_id)
            file_url = new_file.file_path
            
            # 2. Transcribe via Deepgram URL source
            # Using Deepgram Python SDK v3 structure found via inspection
            # self.deepgram.listen.v1.media.transcribe_url uses keyword arguments
            # Run in thread to avoid blocking asyncio loop
            
            response = await asyncio.to_thread(
                self.deepgram.listen.v1.media.transcribe_url,
                url=file_url,
                model="nova-2",
                language="hi",
                smart_format=True,
            )
            
            transcript = response.results.channels[0].alternatives[0].transcript
            logger.info(f"Deepgram Transcript: {transcript}")
            return transcript

        except Exception as e:
            logger.error(f"Transcription Error: {e}")
            return ""

    async def _request_location(self, chat_id: int, message: str = "आपकी location भेजें 📍"):
        """
        Send a message with a location request button.
        """
        location_button = KeyboardButton(text="📍 Send My Location", request_location=True)
        # resize_keyboard=True makes the button smaller
        # one_time_keyboard=True hides it after use
        keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
        await self.bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)

    def _get_session(self, chat_id: int) -> Dict[str, Any]:
        """
        Get or create a session for the user.
        """
        if chat_id not in self.sessions:
            self.sessions[chat_id] = {
                "history": [],
                "verified": False,
                "driver_details": None
            }
        return self.sessions[chat_id]

    async def _generate_response(self, text: str, chat_id: int, user_phone: str = "+11234567890") -> str:
        """
        Use LLM to generate Raju's response with Tool Support and Session Memory.
        """
        if not self.llm_service.client:
            return "नमस्ते! अभी सर्वर व्यस्त है। (LLM Unavailable)"

        session = self._get_session(chat_id)
        
        try:
            # 1. Build Context Injection
            verification_status = "**STATUS**: UNVERIFIED (Ask for ID)"
            if session["verified"]:
                d = session["driver_details"]
                verification_status = f"**STATUS**: VERIFIED ✅\n- **Driver Name**: {d.get('name')}\n- **Driver ID**: {d.get('id')}\n- **Plan**: {d.get('plan')}"
            
            context_injection = f"""
            
            **CURRENT CONTEXT**:
            - **Customer Phone**: {user_phone} (Caller ID only)
            - {verification_status}
            - **Tools**: You have access to tools. USE THEM when needed.
            
            **CONVERSATION GUIDELINES**:
            1. **BE CONVERSATIONAL**: First acknowledge and address the user's concern/question in natural Hindi.
            2. **EMPATHY FIRST**: If user describes a problem (smoke, damage, battery issue), address their concern and give safety advice FIRST. Do NOT immediately ask for location.
            3. **LOCATION REQUEST**: If user asks for nearest station/DSK:
               - **CHECK**: Do you know their location?
               - **IF NO**: Call `request_user_location` tool. This sends a button to the user.
               - **IF YES**: Call `get_nearest_station`.
            4. **Tool Usage**:
               - verify_driver_by_id: **MANDATORY** for any account/balance/plan query.
               - get_driver_profile: **FORBIDDEN** until Driver ID is verified.
               - request_user_location: Use when you need user's GPS.
               - get_nearest_station: ONLY when you have coordinates.
            """
            
            # 2. Build Message History
            # Start with System Prompt + Context
            messages = [{"role": "system", "content": self.system_prompt + context_injection}]
            
            # Append Session History (Last 10 messages)
            messages.extend(session["history"][-10:])
            
            # Append Current User Message
            messages.append({"role": "user", "content": text})
            
            # 3. First Call to LLM
            completion = self.llm_service.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.6,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )
            
            response_message = completion.choices[0].message
            
            # 4. Handle Tool Calls (Structured + Text Fallback)
            tool_calls = response_message.tool_calls if response_message.tool_calls else []
            
            # Fallback for text-based tool calls
            import re
            content = response_message.content or ""
            regex = r"<function=(\w+)>(.*?)</function>"
            matches = re.findall(regex, content)
            
            if matches and not tool_calls:
                logger.info(f"Found {len(matches)} text-based tool calls")
                class MockToolCall:
                    def __init__(self, id, name, args):
                        self.id = id
                        self.function = type('obj', (object,), {'name': name, 'arguments': args})
                tool_calls = []
                for idx, (func_name, args_str) in enumerate(matches):
                    tool_calls.append(MockToolCall(f"call_text_{idx}", func_name, args_str))
            
            final_response_text = ""

            if tool_calls:
                # Add the assistant's request to messages
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse args for {func_name}: {tool_call.function.arguments}")
                        continue
                    
                    print(f"🔧 Telegram Tool Exec: {func_name} | Args: {args}")
                    
                    result = {"error": "Function not found"}
                    
                    try:
                        # Execute Tool
                        if func_name == "verify_driver_by_id":
                            result = verify_driver_by_id(args.get("driver_id"), args.get("name"))
                            # UPDATE SESSION STATE
                            if result.get("verified"):
                                session["verified"] = True
                                session["driver_details"] = result.get("details")
                                logger.info(f"Session {chat_id} VERIFIED as {result.get('name')}")

                        elif func_name == "request_user_location":
                            # Telegram Specific: Send the button
                            # We await handling it as a side effect
                            await self._request_location(chat_id, "📍 Kripya button dabakar apni location share karein 👇")
                            result = {"status": "request_sent", "message": "Location request button sent to user."}

                        elif func_name == "get_driver_profile":
                            if not session["verified"]:
                                result = {"error": "DRIVER NOT VERIFIED. Please ask user for Driver ID first."}
                            else:
                                result = get_driver_profile(args.get("phone_number"))
                                
                        elif func_name == "get_swap_history":
                            if not session["verified"]:
                                result = {"error": "DRIVER NOT VERIFIED. Please ask user for Driver ID first."}
                            else:
                                result = get_swap_history(args.get("phone_number"))

                        elif func_name == "get_nearest_station":
                            result = get_nearest_station(lat=args.get("lat"), lon=args.get("lon"), location_name=args.get("location_name"))
                            if "stations" in result and result["stations"]:
                                try:
                                    stn = result["stations"][0]
                                    lat, lon = stn["location"]["lat"], stn["location"]["lon"]
                                    if self.bot and chat_id:
                                        await self.bot.send_location(chat_id=chat_id, latitude=lat, longitude=lon)
                                except Exception as e:
                                    logger.error(f"Failed to send location pin: {e}") 

                        elif func_name == "get_nearest_dsk":
                            result = get_nearest_dsk(lat=args.get("lat"), lon=args.get("lon"), location_name=args.get("location_name"))
                        elif func_name == "update_driver_location":
                             loc_name = args.get("location_name")
                             result = driver_sim.set_location_by_name(loc_name)
                        elif func_name == "get_plan_details":
                            result = get_plan_details(args.get("plan_name"))
                        elif func_name == "check_penalty_status":
                            result = check_penalty_status(args.get("phone_number"))
                        elif func_name == "report_issue":
                            result = report_issue(args.get("issue_type"), args.get("description"), args.get("customer_phone"))
                        elif func_name == "escalate_to_agent":
                            result = escalate_to_agent(args.get("reason"), args.get("customer_phone"))
                    except Exception as e:
                        result = {"error": str(e)}

                    # Append tool result
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": json.dumps(result)
                    })
                
                # 5. Second Call to LLM (for final answer)
                logger.info("Sending tool results back to LLM...")
                final_completion = self.llm_service.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.3-70b-versatile",
                    temperature=0.7
                )
                final_response_text = final_completion.choices[0].message.content
            else:
                # No tools, just text
                clean_content = re.sub(r"<function=.*?>.*?</function>", "", response_message.content or "").strip()
                final_response_text = clean_content

            # 6. Update History
            session["history"].append({"role": "user", "content": text})
            session["history"].append({"role": "assistant", "content": final_response_text})
            
            return final_response_text

        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return "माफ़ कीजिए, तकनीकी खराबी है। कृपया थोड़ी देर बाद प्रयास करें।"
