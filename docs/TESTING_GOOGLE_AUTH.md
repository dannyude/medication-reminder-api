# Testing Google Sign-In

## Method 1: Using the Test HTML Page (Easiest)

1. **Update the Google Client ID** in `frontend/google-test.html`:
   ```javascript
   const GOOGLE_CLIENT_ID = "YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com";
   ```

2. **Start your API**:
   ```powershell
   uvicorn main:app --reload
   ```

3. **Open the test page**:
   - Option A: Serve via a simple HTTP server:
     ```powershell
     cd frontend
     python -m http.server 8080
     ```
     Then visit: `http://localhost:8080/google-test.html`

   - Option B: Add static file serving to your FastAPI app (see below)

4. **Click "Sign in with Google"** and watch the console/results

---

## Method 2: Using Postman/Thunder Client

1. **Get a real Google ID token**:
   - Go to [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
   - Click the gear icon (⚙️) → Check "Use your own OAuth credentials"
   - Enter your Client ID and Client Secret
   - In Step 1: Select "Google OAuth2 API v2" → `https://www.googleapis.com/auth/userinfo.email`
   - Click "Authorize APIs"
   - In Step 2: Click "Exchange authorization code for tokens"
   - Copy the `id_token` from the response

2. **Test the endpoint**:
   ```http
   POST http://localhost:8000/auth/google
   Content-Type: application/json

   {
     "id_token": "YOUR_GOOGLE_ID_TOKEN_HERE"
   }
   ```

---

## Method 3: Using cURL

```powershell
$idToken = "YOUR_GOOGLE_ID_TOKEN"

$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/google" `
  -Method POST `
  -ContentType "application/json" `
  -Body (@{id_token = $idToken} | ConvertTo-Json)

$response | ConvertTo-Json
```

---

## Adding Static File Serving to FastAPI

To serve the test HTML directly from your API:

**In `main.py`**, add:
```python
from fastapi.staticfiles import StaticFiles

# After creating your app
app.mount("/static", StaticFiles(directory="frontend"), name="static")
```

Then visit: `http://localhost:8000/static/google-test.html`

---

## Expected Response

Success:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

Error:
```json
{
  "detail": "Invalid Google Token"
}
```

---

## Troubleshooting

1. **"Invalid Google Token"** → Token expired or wrong Client ID
2. **CORS errors** → Add CORS middleware to your FastAPI app
3. **"Could not verify audience"** → Client ID mismatch between frontend and backend
4. **"Google email not verified"** → Use a verified Google account
