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
    get_plan_details
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
        You speak in **PURE HINDI** (Devanagari) but use English for technical terms (Battery, Station, App).
        
        **Tone**: Polite, Desi, Helpful.
        **Example**: "नमस्ते सर! मैं राजू हूँ। बताइए क्या सेवा करूँ?"
        
        If the user sends audio, acknowledge you heard them.
        Keep responses short (under 50 words) for chat.
        """

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
            # Using Deepgram Python SDK v3 with dict options
            
            source = {"url": file_url}
            options = {
                "model": "nova-2",
                "language": "hi",
                "smart_format": True,
            }
            
            response = self.deepgram.listen.prerecorded.v("1").transcribe_url(
                source, options
            )
            
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript

        except Exception as e:
            logger.error(f"Transcription Error: {e}")
            return ""

    async def _request_location(self, chat_id: int, message: str = "आपकी location भेजें 📍"):
        """
        Send a message with a location request button.
        """
        location_button = KeyboardButton(text="📍 Send My Location", request_location=True)
        keyboard = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
        await self.bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)

    async def _generate_response(self, text: str, chat_id: int, user_phone: str = "+11234567890") -> str:
        """
        Use LLM to generate Raju's response with Tool Support.
        """
        if not self.llm_service.client:
            return "नमस्ते! अभी सर्वर व्यस्त है। (LLM Unavailable)"

        try:
            # 1. Inject Context
            context_injection = f"""
            
            **CURRENT CONTEXT**:
            - **Customer Phone**: {user_phone}
            - **Tools**: You have access to tools. USE THEM when needed.
            
            **CONVERSATION GUIDELINES**:
            1. **BE CONVERSATIONAL**: First acknowledge and address the user's concern/question in natural Hindi.
            2. **EMPATHY FIRST**: If user describes a problem (smoke, damage, battery issue), address their concern and give safety advice FIRST. Do NOT immediately ask for location.
            3. **NATURAL FLOW**: After addressing their concern, if they need to visit a station, ask in natural Hindi: "Aap abhi kahan hain? Mujhe bataiye toh main aapko najdiki station dhundhta hoon."
            4. **DON'T ASSUME LOCATION**: Only call get_nearest_station when user has explicitly told you their location (e.g., "main Rajouri mein hoon").
            5. **Tool Usage**:
               - get_driver_profile: For account/balance queries
               - get_nearest_station: ONLY when you have a confirmed location name or coordinates from user
               - get_plan_details: For subscription/pricing queries
            """
            
            messages = [
                {"role": "system", "content": self.system_prompt + context_injection},
                {"role": "user", "content": text}
            ]
            
            # 2. First Call to LLM
            completion = self.llm_service.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.6,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )
            
            response_message = completion.choices[0].message
            
            # 3. Handle Tool Calls (Structured + Text Fallback)
            tool_calls = response_message.tool_calls if response_message.tool_calls else []
            
            # Fallback: Check for Llama-style text tool calls like <function=name>{args}</function>
            import re
            content = response_message.content or ""
            regex = r"<function=(\w+)>(.*?)</function>"
            matches = re.findall(regex, content)
            
            if matches and not tool_calls:
                # If we found text-based tool calls but no structured ones, parse them
                logger.info(f"Found {len(matches)} text-based tool calls")
                
                # Create a mock tool call object for consistency
                class MockToolCall:
                    def __init__(self, id, name, args):
                        self.id = id
                        self.function = type('obj', (object,), {'name': name, 'arguments': args})
                
                tool_calls = []
                for idx, (func_name, args_str) in enumerate(matches):
                    tool_calls.append(MockToolCall(f"call_text_{idx}", func_name, args_str))
                    
                # Clean the content to remove the tags for the user (if we weren't doing a 2nd pass)
                # But since we ARE doing a 2nd pass, we just need to append the "assistant" message correctly.
                # Ideally, we should simulate the assistant sending the tool call.
            
            if tool_calls:
                # Add the assistant's request to messages
                # If it was a text match, we should probably add the ORIGINAL content to history
                # so the model knows what it 'wrote'. 
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
                        if func_name == "get_driver_profile":
                            result = get_driver_profile(args.get("phone_number"))
                        elif func_name == "get_swap_history":
                            result = get_swap_history(args.get("phone_number"))
                        elif func_name == "get_nearest_station":
                            result = get_nearest_station(
                                lat=args.get("lat"), 
                                lon=args.get("lon"),
                                location_name=args.get("location_name")
                            )
                            # Visual Feedback: Send Pin
                            if "stations" in result and result["stations"]:
                                try:
                                    stn = result["stations"][0]
                                    lat, lon = stn["location"]["lat"], stn["location"]["lon"]
                                    if self.bot and chat_id:
                                        await self.bot.send_location(chat_id=chat_id, latitude=lat, longitude=lon)
                                except Exception as e:
                                    logger.error(f"Failed to send location pin: {e}") 

                        elif func_name == "get_nearest_dsk":
                            result = get_nearest_dsk(
                                lat=args.get("lat"), 
                                lon=args.get("lon"),
                                location_name=args.get("location_name")
                            )
                        elif func_name == "update_driver_location":
                             loc_name = args.get("location_name")
                             result = driver_sim.set_location_by_name(loc_name)
                        elif func_name == "get_plan_details":
                            result = get_plan_details(args.get("plan_name"))
                    except Exception as e:
                        result = {"error": str(e)}

                    # Append tool result
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": json.dumps(result)
                    })
                
                # 4. Second Call to LLM (for final answer)
                logger.info("Sending tool results back to LLM...")
                final_completion = self.llm_service.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.3-70b-versatile",
                    temperature=0.7
                )
                return final_completion.choices[0].message.content
            
            # If no tools invoked, verify content doesn't have leftover tags (just in case)
            clean_content = re.sub(r"<function=.*?>.*?</function>", "", response_message.content or "").strip()
            return clean_content


        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return "माफ़ कीजिए, तकनीकी खराबी है। कृपया थोड़ी देर बाद प्रयास करें।"
