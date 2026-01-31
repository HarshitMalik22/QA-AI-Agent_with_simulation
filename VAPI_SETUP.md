# Vapi Phone Number Integration Guide

## 1. Expose Your Backend
To allow Vapi to communicate with your local backend, you need to expose port 8000 to the internet.
Use **ngrok** (or similar):

```bash
ngrok http 8000
```

Copy the HTTPS URL generated (e.g., `https://abcd-1234.ngrok.io`).

## 4. Option B: Using Twilio (Indian Number - READ CAREFULLY)
**Status**: 🔴 **EXTREMELY DIFFICULT FOR HACKATHONS**
To get an Indian (`+91`) number on Twilio, you are **legally required** to submit:
1.  **Business Registration** (GSTIN / PAN).
2.  **Proof of Address**.
3.  **Authorized Signatory Letter**.
4.  **Wait Time**: Verification takes **24-72 hours**.

**If you already have a verified Twilio India account:**
1.  Buy the +91 number in Twilio.
2.  Go to Vapi -> Provider Credentials -> Add Twilio (SID/Auth Token).
3.  Vapi -> Phone Numbers -> Import from Twilio.
4.  Set the `Server URL` to your ngrok link as described in step 2.

---

## 5. The "Hackathon Cheat Code" (Recommended) 💡
Since getting an Indian number instantly is impossible without prior verification, do this to make it **LOOK** like an Indian Support Line:

1.  **Buy a US Number on Vapi** (starts with +1).
2.  **Save it in your phone contacts** as **"Battery Smart Priority Support"**.
3.  **The Demo Flow**:
    - "Let me call our support line..."
    - Open Contacts -> Search "Battery Smart".
    - Tap Call.
    - Result: screen shows **"Battery Smart Priority Support"** calling.
    - Everyone hears "Namaste Sir! Main Raju..." in Hindi.
    - **Outcome**: Judges see the name, hear the Hindi voice, and assume it's local. The code (`+1`) is hidden by the saved contact name.
