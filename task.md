# Vapi Integration Checklist

- [x] **Backend Integration**
  - [x] Create `/api/vapi/assistant` endpoint
  - [x] Create `/api/vapi/webhook` endpoint
  - [x] Implement `perform_analysis` logic
  - [x] Switch to Azure Voice (Hindi)
- [x] **Frontend Integration**
  - [x] Add Polling for `/api/analysis/latest`
  - [x] Update UI to show analysis from phone calls
- [x] **Infrastructure**
  - [x] Install `ngrok`
  - [x] Authenticate `ngrok`
- [ ] **Final Configuration**
  - [ ] Run `ngrok http 8000`
  - [ ] Update Vapi Dashboard with ngrok URL
  - [ ] Verify call flow
