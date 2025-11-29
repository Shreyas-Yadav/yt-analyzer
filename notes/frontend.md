# Frontend Documentation

## 1. Overview
The frontend is a **React Single Page Application (SPA)** built with **Vite** and styled with **TailwindCSS**. It serves as the user interface for the YT-Analyzer platform, handling user authentication, video submission, and displaying analysis results (Flashcards, Quizzes, Transcripts).

## 2. Project Structure
```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── YouTubeInput.jsx  # URL submission form
│   │   └── ...
│   ├── config/           # Configuration files
│   │   └── api.js        # API Base URL logic
│   ├── pages/            # Page components (Routes)
│   │   ├── Dashboard.jsx # Main user dashboard
│   │   ├── Login.jsx     # Sign In page (with Turnstile)
│   │   ├── Signup.jsx    # Sign Up page (with Turnstile)
│   │   └── ...
│   ├── services/         # API Service layer
│   │   ├── AuthService.js    # Cognito wrapper
│   │   └── VideoService.js   # Backend API wrapper
│   ├── App.jsx           # Main App component & Routing
│   └── main.jsx          # Entry point
├── .env                  # Dev environment variables
├── .env.production       # Prod environment variables
└── package.json          # Dependencies
```

## 3. Authentication (Cognito + Turnstile)
We use **AWS Cognito** for identity management and **Cloudflare Turnstile** for bot protection.

### Flow
1.  **User Visits Login/Signup**:
    -   The `Turnstile` widget renders.
    -   The "Sign In/Up" button is **disabled**.
2.  **Verification**:
    -   User completes the Turnstile challenge (often invisible).
    -   Turnstile returns a token -> Button becomes **enabled**.
3.  **Submission**:
    -   **Email/Password**: `AuthService` calls Cognito User Pool.
    -   **Google OAuth**: Redirects to Cognito Hosted UI (`/oauth2/authorize`).
4.  **Session**:
    -   Cognito stores tokens (Access, ID, Refresh) in LocalStorage.
    -   `AuthService.isAuthenticated()` checks for valid tokens.

## 4. State Management
-   **Local State**: Used for form inputs and UI toggles (e.g., `useState` in `Login.jsx`).
-   **Data State**: `Dashboard.jsx` manages the list of videos.
    -   **Polling**: The dashboard polls the API every 3 seconds if any video is in `queued` or `processing` state to update the UI automatically.

## 5. API Integration
All backend communication is centralized in `src/services/`.

### `AuthService.js`
-   Wraps `aws-amplify/auth` methods.
-   Handles `signIn`, `signUp`, `signOut`, and `signInWithRedirect` (Google).

### `VideoService.js` (and direct fetch in Dashboard)
-   **Base URL**: Loaded from `VITE_API_BASE_URL`.
-   **Endpoints**:
    -   `POST /analyze`: Submit a URL.
    -   `GET /videos`: List user's videos.
    -   `DELETE /videos/:id`: Remove a video.

## 6. Deployment
-   **Build**: `npm run build` (Vite produces optimized static assets in `dist/`).
-   **Host**: AWS S3 (`shri.software` bucket).
-   **Routing**: S3 Error Document set to `index.html` to support React Router (client-side routing).
