# 🤖 MediScan — AI Build Prompt (Claude Opus 4.6)

> **How to use this file:** Copy the contents of this prompt into a new conversation with an AI coding assistant (Claude Opus 4.6 in VS Code / GitHub Copilot). The AI will build the MediScan Android app step by step, stopping after each phase for your confirmation.

---

## THE PROMPT — Copy Everything Below This Line

---

You are an expert Android developer using **Kotlin** and **Jetpack Compose**. You will build the **MediScan** Android application step by step, following the architecture and specifications exactly as described in the project documents.

### 📚 Required Reading (BEFORE you start coding):

You MUST read and analyze these 3 documents completely before writing any code:

1. **`SYSTEM_DESIGN.md`** — Complete system architecture, tech stack decisions, data flow diagrams, Firebase schema, and architectural patterns (MVVM + Clean Architecture)
2. **`APP_SPECIFICATION.md`** — All 12 screen specifications with wireframes, Kotlin data models, Compose UI requirements, build.gradle.kts dependencies, project file structure, and development order
3. **`BACKEND_API_REFERENCE.md`** — FastAPI endpoints, exact request/response JSON formats, Retrofit2 interface, connection URLs, error handling, and the complete backend code

**Read all three documents thoroughly. Do NOT start coding until you understand the full system.**

---

### 🚨 CRITICAL RULES — Follow These Strictly:

1. **ONE PHASE AT A TIME.** Do not jump ahead. Complete Phase 1 fully before starting Phase 2. Do not create files for future phases.

2. **STOP AND ASK ME** whenever you need me to do something you cannot do (Firebase Console setup, Google Cloud Console, API keys, running `./gradlew`, etc.). Tell me **exactly** what to do, step by step, with screenshots guidance if possible.

3. **TEST EACH PHASE** before moving on. After each phase, tell me how to test it (what to click, what I should see). We only proceed to the next phase when the current one works.

4. **DO NOT create placeholder or stub code.** Every file you create must be functional and complete for that phase.

5. **USE THE EXACT TECH STACK** from `SYSTEM_DESIGN.md`:
   - Kotlin + Jetpack Compose (Material 3)
   - Hilt for dependency injection
   - Navigation Compose for routing
   - Firebase Auth, Firestore, Storage (direct from Android — NO custom backend auth)
   - Retrofit2 + OkHttp for FastAPI connection
   - Room for local cache
   - CameraX for camera
   - Coil for image loading
   - Vico for charts
   - Google Maps Compose for maps
   - WorkManager for reminders

6. **USE THE EXACT PROJECT STRUCTURE** from `APP_SPECIFICATION.md`:
   ```
   app/src/main/java/com/mediscan/
   ├── MediScanApp.kt
   ├── MainActivity.kt
   ├── core/ (constants, theme, navigation, utils)
   ├── data/ (model, remote, local, repository)
   ├── di/ (Hilt modules)
   ├── ui/ (viewmodel, screens, components)
   └── service/ (ReminderWorker)
   ```

7. **PACKAGE NAME:** `com.mediscan.app`

8. **TELL ME WHAT YOU'RE DOING.** Before each file, explain what it does and why. After creating files, give me a summary of what was built and what to test.

---

### 📋 BUILD PHASES — Execute In This Exact Order:

---

#### **PHASE 1: Project Setup + Theme + Navigation Shell**

**What to build:**
- New Android project: `com.mediscan.app`, min SDK 26, target SDK 34
- `build.gradle.kts` (project + module) with ALL dependencies from `APP_SPECIFICATION.md`
- Hilt setup: `MediScanApp.kt` (@HiltAndroidApp), `MainActivity.kt` (@AndroidEntryPoint)
- Theme: `Color.kt`, `Type.kt`, `Theme.kt` (MediScanTheme with Material 3)
- Navigation: `NavGraph.kt` with all route definitions (empty screens for now)
- `NetworkResult.kt` sealed class
- `ApiEndpoints.kt` constants

**What to test:** App launches → shows a blank themed screen with no crashes. Logcat shows Hilt initialization.

**⏸️ STOP after Phase 1.** Ask me: "Phase 1 is complete. Run the app. Does it launch without errors? If yes, say 'next' and I'll build Phase 2."

---

#### **PHASE 2: Authentication (Login + SignUp + Firebase)**

**What to build:**
- `LoginScreen.kt` — Full UI matching wireframe from `APP_SPECIFICATION.md`
- `SignUpScreen.kt` — Full UI with patient/doctor role toggle
- `SplashScreen.kt` — Logo + auth state check
- `AuthViewModel.kt` — Firebase email + Google Sign-In logic
- `AuthRepository.kt` — Firebase Auth wrapper
- `User.kt` data model
- Firestore write on signup (save user to `users/{uid}`)
- Navigation: Splash → Login/SignUp → PatientMain or DoctorMain (based on role)

**🔧 STOP AND TELL ME TO DO THIS:**
Before this phase works, I need to:
1. Create a Firebase project at https://console.firebase.google.com/
2. Add Android app with package `com.mediscan.app`
3. Download `google-services.json` and put it in the `app/` folder
4. Enable Email/Password auth in Firebase Console → Authentication → Sign-in method
5. Enable Google Sign-In provider in Firebase Console
6. Get SHA-1 fingerprint: run `./gradlew signingReport` in Android Studio terminal
7. Add SHA-1 to Firebase Console → Project Settings → Android app → SHA certificate fingerprints
8. Create Firestore database in Firebase Console → Firestore → Create database → Test mode
9. Enable Firebase Storage in Firebase Console → Storage → Get started → Test mode

**Tell me the exact steps above before coding. Wait for me to confirm I've done them.**

**What to test:**
- Open app → Splash screen shows for 2 seconds → redirects to Login
- Register a new patient account → lands on Patient screen
- Logout → Login again with same credentials
- Register a doctor account → lands on Doctor screen
- Check Firebase Console → Authentication tab shows the user
- Check Firestore → `users` collection has the user document

**⏸️ STOP after Phase 2.** Wait for my confirmation that auth works.

---

#### **PHASE 3: Patient Bottom Navigation + Home Screen**

**What to build:**
- `PatientMainScreen.kt` — Bottom navigation with 4 tabs (Home, Scan, Docs, Profile)
- `PatientHomeScreen.kt` — Full UI: greeting, upcoming appointments (mock data for now), action cards
- Placeholder screens for other tabs (just centered text showing tab name)
- Bottom nav icons, active/inactive states

**What to test:**
- After login as patient → bottom navigation visible with 4 tabs
- Home tab shows greeting + cards
- Can switch between tabs
- Back button on Home exits app (not going to login)

**⏸️ STOP after Phase 3.**

---

#### **PHASE 4: Scan Screen + CameraX + FastAPI Connection**

**What to build:**
- `ScanScreen.kt` — Initial state with tips card and scan button
- CameraX integration — full camera preview, capture photo
- `FastApiService.kt` — Retrofit interface
- `NetworkModule.kt` — Hilt module with OkHttp + Retrofit
- `ScanViewModel.kt` — Send image to FastAPI, handle response
- `ExtractionResultSheet.kt` — Bottom sheet showing extracted medications (editable)
- `ExtractionResult.kt` and all related data models from `APP_SPECIFICATION.md`
- Camera permission handling (Accompanist)
- Base64 encoding and API call

**🔧 STOP AND TELL ME TO DO THIS:**
1. Start the FastAPI server on my PC:
   ```
   cd N:\Capstone Project\prescription_ai
   python backend/fastapi_app.py
   ```
2. Wait for "API Server Ready!" message
3. If using emulator: base URL is `http://10.0.2.2:8000/`
4. If using physical device: find PC's WiFi IP (`ipconfig`) and use `http://192.168.x.x:8000/`
5. Verify: open `http://localhost:8000/health` in browser — should show JSON

**What to test:**
- Go to Scan tab → see tips and scan button
- Tap scan → camera opens (grant permission if asked)
- Take photo of a prescription → "Analyzing..." loading
- Results appear in bottom sheet with medications
- Edit a medication field → Save button works
- If bad quality → error message with retake option

**⏸️ STOP after Phase 4.**

---

#### **PHASE 5: Save Prescriptions to Firestore + Docs Screen**

**What to build:**
- `PrescriptionRepository.kt` — Save/read/delete prescriptions in Firestore
- Upload prescription image to Firebase Storage
- `PrescriptionViewModel.kt`
- `DocsScreen.kt` — List of saved prescriptions with search/filter
- Prescription detail screen (view full extraction + original image)
- Delete prescription with confirmation dialog
- `PrescriptionCard.kt`, `MedicationCard.kt` components

**What to test:**
- Scan a prescription → Save → appears in Docs tab
- Open saved prescription → all data shows correctly
- Original image loads from Firebase Storage
- Delete a prescription → disappears from list
- Close app → reopen → prescriptions still there

**⏸️ STOP after Phase 5.**

---

#### **PHASE 6: Patient Profile**

**What to build:**
- `PatientProfileScreen.kt` — Profile menu
- Edit profile screen (name, phone, DOB, blood group, address, emergency contact)
- Change password (Firebase Auth)
- Upload/change profile photo (Firebase Storage)
- Logout function → clear back stack → Login screen

**What to test:**
- Profile tab shows user info
- Edit profile → save → data persists
- Change profile photo → shows new image
- Logout → returns to login → login again → profile data intact

**⏸️ STOP after Phase 6.**

---

#### **PHASE 7: Doctor Portal**

**What to build:**
- `DoctorMainScreen.kt` — Bottom navigation (3 tabs: Appointments, Records, Profile)
- `DoctorAppointmentsScreen.kt` — Appointment list with status management
- `DoctorRecordsScreen.kt` — Analytics with Vico chart + patient list
- `DoctorProfileScreen.kt` — Same as patient + hospital/timings/fee fields
- `AppointmentViewModel.kt`, `DoctorViewModel.kt`
- `Appointment.kt` data model

**What to test:**
- Login as doctor → 3-tab navigation
- Appointments screen shows list (empty initially)
- Records screen shows charts (mock data initially)
- Doctor profile shows extra fields

**⏸️ STOP after Phase 7.**

---

#### **PHASE 8: Appointment Booking System**

**What to build:**
- Patient side: Search doctors, view doctor profiles, book appointment with date/time picker
- Doctor side: See incoming appointments, accept/cancel
- `AppointmentRepository.kt` — Firestore CRUD for appointments
- Real-time updates using Firestore snapshots

**What to test:**
- Patient searches for a doctor → books appointment
- Doctor sees the appointment in their list
- Doctor accepts → status updates for patient
- Cancel works from both sides

**⏸️ STOP after Phase 8.**

---

#### **PHASE 9: Google Maps Integration**

**What to build:**
- Nearby Hospitals screen with Google Maps Compose
- Current location detection
- Hospital markers from Google Places API
- Info window on marker tap

**🔧 STOP AND TELL ME TO DO THIS:**
1. Go to Google Cloud Console → Enable "Maps SDK for Android" and "Places API"
2. Create an API key → restrict to Android apps → add SHA-1 + package name
3. Put API key in `AndroidManifest.xml`

**⏸️ STOP after Phase 9.**

---

#### **PHASE 10: Medication Reminders**

**What to build:**
- `ReminderWorker.kt` — WorkManager periodic task
- Notification channel setup
- Reminder creation from saved medications
- Notification at scheduled times

**What to test:**
- Save a prescription → set reminder → notification fires

**⏸️ STOP after Phase 10.**

---

#### **PHASE 11: Polish & Final**

**What to build:**
- Loading shimmer effects on lists
- Pull-to-refresh on Docs and Appointments
- Error states with retry buttons
- Empty states with illustrations
- Transition animations between screens
- App icon and splash screen branding
- ProGuard rules for release build

**⏸️ FINAL STOP.** App is complete.

---

### 🎯 Summary of When You Need Me:

| Phase | What I Need to Do |
|-------|------------------|
| **Phase 2** | Create Firebase project, download `google-services.json`, enable Auth/Firestore/Storage, add SHA-1 |
| **Phase 4** | Start FastAPI server on my PC, verify `/health` endpoint works |
| **Phase 9** | Enable Maps/Places API in Google Cloud Console, create API key |
| Every Phase | Run the app and confirm it works before you proceed |

---

### 🔄 How We Communicate:

After each phase:
1. You tell me what you built
2. You tell me how to test it (exact steps)
3. You ask if there's anything I need to do manually
4. I confirm everything works
5. I say **"next"** and you proceed to the next phase

**If something breaks:** Tell me the exact error and how to fix it before moving on.

**If you need something from me:** Tell me exactly what to do, step by step, like I'm a beginner.

---

**NOW START WITH PHASE 1.**

Read the three documents (`SYSTEM_DESIGN.md`, `APP_SPECIFICATION.md`, `BACKEND_API_REFERENCE.md`) and begin building Phase 1: Project Setup + Theme + Navigation Shell.
