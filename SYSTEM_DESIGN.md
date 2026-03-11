# 🏗️ System Design: MediScan
## AI-Powered Prescription Digitization & Smart Medicine Management System

> **Last Updated:** February 24, 2026 — Final architecture (Kotlin/Compose + Firebase + FastAPI)

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                      MEDISCAN                                        │
│                         Smart Prescription Management System                         │
│                              (English Extraction Only)                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                         │
                    ▼                                         ▼
            ┌──────────────┐                          ┌──────────────┐
            │   PATIENT    │                          │    DOCTOR    │
            │ Android App  │                          │ Android App  │
            │ Kotlin/Compose│                         │ Kotlin/Compose│
            └──────┬───────┘                          └──────┬───────┘
                    │                                         │
                    │         (Same APK, role-based UI)       │
                    └────────────────────┬────────────────────┘
                                         │
                          ┌──────────────┼──────────────┐
                          │              │              │
                          ▼              ▼              ▼
                   ┌───────────┐  ┌───────────┐  ┌───────────┐
                   │ Firebase  │  │ Firebase  │  │ Firebase  │
                   │   Auth    │  │ Firestore │  │  Storage  │
                   │(login/reg)│  │ (database)│  │ (images)  │
                   └───────────┘  └───────────┘  └───────────┘
                                         │
                                         │ (Prescription extraction only)
                                         ▼
                          ┌─────────────────────────────┐
                          │     ⚡ FASTAPI BACKEND       │
                          │   (AI Extraction Server)     │
                          │      Port: 8000              │
                          ├─────────────────────────────┤
                          │  🔍 Quality Checker          │
                          │  🎯 YOLOv8s (9 classes)      │
                          │  📝 PaddleOCR (English)      │
                          │  🧩 Spatial Medication Grouping│
                          └─────────────────────────────┘
```

### Architecture Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Single app or separate apps? | **Single APK** with role-based UI | Simpler to maintain, shared auth logic |
| Where to store user data? | **Firebase Firestore** (cloud) | Real-time sync, offline cache, free tier, no server setup |
| Where to store images? | **Firebase Storage** | Secured by Firebase Auth UID, 5GB free |
| Where to run AI? | **FastAPI server** (your laptop or cloud) | GPU needed for YOLO + PaddleOCR, too heavy for mobile |
| Auth system? | **Firebase Auth** only | Native Android SDK, Google Sign-In built-in, no custom JWT needed |
| Local offline cache? | **Room (SQLite)** | Official Jetpack, Kotlin coroutines, compile-time SQL checks |

---

## 🎯 Component Details

### 1️⃣ CLIENT LAYER — Android App (Kotlin + Jetpack Compose)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        📱 ANDROID APPLICATION                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  One APK — Two Roles:                                                   │
│                                                                         │
│  📱 PATIENT ROLE                    👨‍⚕️ DOCTOR ROLE                      │
│  ─────────────                     ─────────────                        │
│  • Camera capture (CameraX)        • View patients list                 │
│  • Upload prescription image       • Search patients                    │
│  • View extracted medications      • View patient Rx history            │
│  • Medication reminders            • View all medications               │
│  • Prescription history            • Digital prescription writing       │
│  • Book appointments               • Patient diagnosis history          │
│  • Buy medicines (browse)          • Analytics dashboard (Vico charts)  │
│  • Nearby hospitals (Maps)         • Appointment management             │
│  • Profile management              • Profile management                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Tech Stack (Android):

| Category | Library | Version | Purpose |
|----------|---------|---------|---------|
| **Language** | Kotlin | 1.9+ | Primary language |
| **UI Framework** | Jetpack Compose | Material 3 | Declarative UI |
| **Architecture** | MVVM + Clean Architecture | — | Separation of concerns |
| **DI** | Hilt (Dagger) | 2.50+ | Dependency injection |
| **HTTP Client** | Retrofit2 + OkHttp | 2.9+ / 4.12+ | API calls to FastAPI |
| **Auth** | Firebase Auth | latest | Email/password + Google Sign-In |
| **Cloud DB** | Firebase Firestore | latest | User data, prescriptions, appointments |
| **Cloud Storage** | Firebase Storage | latest | Prescription images |
| **Local DB** | Room (SQLite) | 2.6+ | Offline cache |
| **Camera** | CameraX | 1.3+ | Prescription photo capture |
| **Image Loading** | Coil | 2.5+ | Async image loading (Compose-native) |
| **Navigation** | Navigation Compose | 2.7+ | Screen routing |
| **Charts** | Vico | 2.0+ | Doctor analytics (Compose-native) |
| **Maps** | Google Maps Compose | 4.3+ | Hospital/pharmacy finder |
| **Notifications** | WorkManager + FCM | latest | Local reminders + push notifications |
| **Token Storage** | EncryptedSharedPreferences | latest | Secure local storage |
| **Serialization** | Kotlinx Serialization or Gson | latest | JSON parsing |

#### Android Project Structure:

```
app/src/main/java/com/mediscan/
├── MediScanApp.kt                      # Application class (@HiltAndroidApp)
├── MainActivity.kt                      # Single Activity (Compose)
│
├── core/
│   ├── constants/
│   │   ├── AppColors.kt                # Color palette
│   │   ├── AppStrings.kt               # String constants
│   │   └── ApiEndpoints.kt             # FastAPI base URL + endpoints
│   ├── theme/
│   │   ├── Theme.kt                    # Material 3 Theme
│   │   ├── Color.kt                    # Color definitions
│   │   └── Type.kt                     # Typography (Poppins + Roboto)
│   ├── navigation/
│   │   └── NavGraph.kt                 # Navigation Compose routes
│   └── utils/
│       ├── Validators.kt               # Email/phone validation
│       ├── DateUtils.kt                # Date formatting
│       └── NetworkResult.kt            # Sealed class for API states
│
├── data/
│   ├── model/
│   │   ├── User.kt                     # Kotlin data class
│   │   ├── Prescription.kt             # Kotlin data class
│   │   ├── Medication.kt               # Kotlin data class
│   │   ├── Appointment.kt              # Kotlin data class
│   │   └── ExtractionResult.kt         # API response model
│   ├── remote/
│   │   ├── FastApiService.kt           # Retrofit interface (AI extraction)
│   │   └── dto/                        # Data Transfer Objects
│   ├── local/
│   │   ├── AppDatabase.kt              # Room database
│   │   └── dao/                        # Room DAOs (PrescriptionDao, etc.)
│   └── repository/
│       ├── AuthRepository.kt           # Firebase Auth operations
│       ├── PrescriptionRepository.kt   # Firestore + FastAPI
│       ├── AppointmentRepository.kt    # Firestore appointments
│       └── UserRepository.kt           # Firestore user data
│
├── di/
│   ├── AppModule.kt                    # Hilt: provides singletons
│   ├── NetworkModule.kt                # Hilt: provides Retrofit + OkHttp
│   └── DatabaseModule.kt              # Hilt: provides Room database
│
├── ui/
│   ├── viewmodel/
│   │   ├── AuthViewModel.kt            # Login/signup state
│   │   ├── PrescriptionViewModel.kt    # Prescription CRUD
│   │   ├── ScanViewModel.kt            # Camera + extraction
│   │   ├── AppointmentViewModel.kt     # Appointments state
│   │   └── DoctorViewModel.kt          # Doctor dashboard state
│   ├── screens/
│   │   ├── splash/
│   │   │   └── SplashScreen.kt
│   │   ├── auth/
│   │   │   ├── LoginScreen.kt
│   │   │   └── SignUpScreen.kt
│   │   ├── patient/
│   │   │   ├── PatientMainScreen.kt    # Bottom nav scaffold
│   │   │   ├── home/
│   │   │   │   └── PatientHomeScreen.kt
│   │   │   ├── scan/
│   │   │   │   └── ScanScreen.kt       # CameraX + extraction
│   │   │   ├── docs/
│   │   │   │   └── DocsScreen.kt       # Prescription history
│   │   │   └── profile/
│   │   │       └── PatientProfileScreen.kt
│   │   └── doctor/
│   │       ├── DoctorMainScreen.kt     # Bottom nav scaffold
│   │       ├── appointments/
│   │       │   └── DoctorAppointmentsScreen.kt
│   │       ├── records/
│   │       │   └── DoctorRecordsScreen.kt  # Analytics + Vico charts
│   │       └── profile/
│   │           └── DoctorProfileScreen.kt
│   └── components/
│       ├── common/
│       │   ├── MediButton.kt
│       │   ├── MediTextField.kt
│       │   ├── LoadingIndicator.kt
│       │   └── MediCard.kt
│       ├── AppointmentCard.kt
│       ├── PrescriptionCard.kt
│       ├── MedicationCard.kt
│       └── ExtractionResultSheet.kt
│
└── service/
    └── ReminderWorker.kt               # WorkManager for medication reminders
```

---

### 2️⃣ AUTHENTICATION — Firebase Auth (Only)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        🔐 AUTHENTICATION FLOW                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📱 Android App                 🔥 Firebase Auth                        │
│       │                              │                                  │
│       │  1. User enters email/       │                                  │
│       │     password OR taps         │                                  │
│       │     "Sign in with Google"    │                                  │
│       │                              │                                  │
│       │  2. Firebase SDK call:       │                                  │
│       │     auth.signInWith...()     │                                  │
│       │ ────────────────────────────▶│                                  │
│       │                              │                                  │
│       │  3. Firebase returns:        │                                  │
│       │     FirebaseUser object      │                                  │
│       │     + ID Token (JWT)         │                                  │
│       │ ◀────────────────────────────│                                  │
│       │                              │                                  │
│       │  4. Store user profile       │                                  │
│       │     in Firestore             │                                  │
│       │     (name, role, phone...)   │                                  │
│       │ ────────────────────────────▶│  Firestore                       │
│       │                              │                                  │
│       │  5. Navigate to Home         │                                  │
│       │     (Patient or Doctor       │                                  │
│       │      based on role field)    │                                  │
│       │                              │                                  │
│       │  ─── For AI API calls ───    │                                  │
│       │                              │                                  │
│       │  6. Get Firebase ID Token:   │                                  │
│       │     user.getIdToken()        │                                  │
│       │                              │                                  │
│       │  7. Send to FastAPI:         │                                  │
│       │     Authorization: Bearer    │                                  │
│       │     <firebase_id_token>      │                                  │
│       │ ──────────────────────────▶  FastAPI verifies with              │
│       │                              firebase-admin SDK                 │
│       │                              │                                  │
└─────────────────────────────────────────────────────────────────────────┘

  ✅ What Firebase Auth gives you for FREE:
  ─────────────────────────────────────────
  • Email/Password registration & login
  • Google Sign-In (one-tap)
  • Password reset emails
  • Email verification
  • Automatic token management (refresh tokens)
  • 10,000 phone verifications/month FREE
  • Unlimited email/password and Google Sign-In users

  ❌ What you DON'T need (removed from old design):
  ──────────────────────────────────────────────────
  • PyJWT / python-jose (Firebase handles tokens)
  • passlib / bcrypt (Firebase handles password hashing)
  • slowapi / Redis rate limiting (not needed for capstone)
  • Custom JWT generation on FastAPI
  • Custom /auth/login, /auth/register endpoints on FastAPI
```

---

### 3️⃣ BACKEND — FastAPI (AI Extraction Server Only)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ⚡ FASTAPI BACKEND                               │
│                   (AI Prescription Extraction Only)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Purpose: Run AI models (YOLO + PaddleOCR) that are too heavy          │
│  for mobile devices. This server does ONE thing: extract data          │
│  from prescription images.                                              │
│                                                                         │
│  📂 Current Structure (already built & working):                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  prescription_ai/                                                │   │
│  │  ├── backend/                                                   │   │
│  │  │   └── fastapi_app.py          # API server V6.1 (READY)     │   │
│  │  │                                                               │   │
│  │  ├── src/                                                       │   │
│  │  │   ├── pipeline/                                              │   │
│  │  │   │   ├── extractor.py         # YOLOv8 + PaddleOCR         │   │
│  │  │   │   └── structured_extractor.py  # Medication grouping    │   │
│  │  │   ├── ocr/                                                   │   │
│  │  │   │   └── paddle_ocr_engine.py # PaddleOCR wrapper          │   │
│  │  │   └── preprocessing/                                         │   │
│  │  │       └── quality_checker.py   # ResNet18 + Laplacian       │   │
│  │  │                                                               │   │
│  │  ├── experiments/v6_9class_english/                              │   │
│  │  │   └── weights/best.pt         # YOLO model (64MB)           │   │
│  │  │                                                               │   │
│  │  └── medicine library/                                          │   │
│  │      └── master_medicine_list.csv # 48,014 medicines           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  🔌 API Endpoints (already implemented in fastapi_app.py):             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  GET  /                       # Server info & version           │   │
│  │  GET  /health                 # Health check                    │   │
│  │  POST /check-quality          # Quality check (file upload)     │   │
│  │  POST /check-quality-base64   # Quality check (base64 string)  │   │
│  │  POST /extract                # Full extraction (file upload)   │   │
│  │  POST /extract-base64         # Full extraction (base64 string)│   │
│  │  GET  /results/{task_id}      # Retrieve saved results          │   │
│  │  DELETE /task/{task_id}       # Delete task data                │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Technologies:                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  • FastAPI 0.109.x          - Web framework                    │    │
│  │  • Uvicorn                  - ASGI server                      │    │
│  │  • python-multipart         - File uploads                     │    │
│  │  • firebase-admin           - Token verification (to add)      │    │
│  │  • CORS enabled             - Android app can connect          │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ⚠️  Note: User data (prescriptions, appointments, profiles) is        │
│  NOT stored in FastAPI. It's all in Firebase Firestore directly         │
│  from the Android app. FastAPI only does AI extraction.                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 4️⃣ AI/ML ENGINE (Already Trained & Working)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        🤖 AI/ML PROCESSING ENGINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      EXTRACTION PIPELINE V6                      │   │
│  │                                                                  │   │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐ │   │
│  │  │  IMAGE   │   │ QUALITY  │   │   YOLO   │   │  PADDLEOCR   │ │   │
│  │  │  INPUT   │──▶│  CHECK   │──▶│ DETECTION│──▶│  (English)   │ │   │
│  │  │          │   │          │   │          │   │              │ │   │
│  │  │ • Photo  │   │• ResNet18│   │ • 9      │   │• Field-spec  │ │   │
│  │  │ • Base64 │   │• Laplacian│  │  classes │   │  preprocess  │ │   │
│  │  │          │   │• 80% acc │   │ • 98.6%  │   │• 3-attempt   │ │   │
│  │  │          │   │          │   │  mAP50   │   │  strategy    │ │   │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────┬───────┘ │   │
│  │                                                       │         │   │
│  │                  ┌────────────────────────────────────┘         │   │
│  │                  ▼                                              │   │
│  │  ┌──────────────────────────────────────┐                       │   │
│  │  │          SPATIAL GROUPING             │                       │   │
│  │  │  Group medications with their doses  │                       │   │
│  │  │  by Y-coordinate proximity           │                       │   │
│  │  └─────────────────────┬────────────────┘                       │   │
│  │                                    ▼                            │   │
│  │                    ┌──────────────────────────┐                 │   │
│  │                    │   STRUCTURED JSON OUTPUT  │                │   │
│  │                    └──────────────────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  9 YOLO Classes:                                                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  MEDICINE  │  DOSE_STRENGTH  │  DOSAGE_SCHEDULE  │  DURATION  │    │
│  │  DOCTOR_NAME  │  HOSPITAL  │  DATE  │  TEST  │  DIAGNOSIS    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Model Files:                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  experiments/v6_9class_english/weights/best.pt   (64 MB)       │    │
│  │  models/image_quality_classifier.pt              (128 MB)      │    │
│  │  medicine library/master_medicine_list.csv        (48K meds)   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  AI Stack:                                                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  • YOLOv8s (Ultralytics)    - Field detection (9 classes)      │    │
│  │  • PaddleOCR 3.2.2          - Text recognition (English)       │    │
│  │  • ResNet18                 - Image quality classification      │    │
│  │  • OpenCV 4.x               - Image preprocessing              │    │
│  │  • PyTorch 2.5.1+cu121      - Deep learning framework          │    │
│  │  • CUDA 12.1                - GPU (NVIDIA GTX 1660, 6GB)       │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 5️⃣ DATABASE — Firebase Firestore (Cloud) + Room (Local)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        🗄️ DATABASE: FIREBASE FIRESTORE                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Why Firestore (not PostgreSQL):                                        │
│  • No server to install/maintain                                       │
│  • Native Android SDK with offline caching built-in                    │
│  • Real-time listeners (data syncs automatically)                      │
│  • Free tier: 1GB storage, 50K reads/day, 20K writes/day              │
│  • Document-based = perfect for prescriptions & user profiles          │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  FIRESTORE COLLECTIONS                                           │   │
│  │                                                                  │   │
│  │  users/{userId}                                                  │   │
│  │  ├── email: String                                              │   │
│  │  ├── fullName: String                                           │   │
│  │  ├── phone: String                                              │   │
│  │  ├── userType: "patient" | "doctor"                             │   │
│  │  ├── profileImageUrl: String?                                   │   │
│  │  ├── createdAt: Timestamp                                       │   │
│  │  │  (Patient-specific)                                           │   │
│  │  ├── dateOfBirth: String?                                       │   │
│  │  ├── bloodGroup: String?                                        │   │
│  │  ├── address: String?                                           │   │
│  │  ├── emergencyContact: String?                                  │   │
│  │  │  (Doctor-specific)                                            │   │
│  │  ├── licenseNumber: String?                                     │   │
│  │  ├── specialization: String?                                    │   │
│  │  ├── hospital: String?                                          │   │
│  │  ├── consultationFee: String?                                   │   │
│  │  ├── availableDays: List<String>?                               │   │
│  │  └── availableTimeRange: String?                                │   │
│  │                                                                  │   │
│  │  prescriptions/{prescriptionId}                                  │   │
│  │  ├── patientId: String (Firebase UID)                           │   │
│  │  ├── doctorName: String?                                        │   │
│  │  ├── hospital: String?                                          │   │
│  │  ├── visitDate: Timestamp                                       │   │
│  │  ├── diagnosis: String?                                         │   │
│  │  ├── medications: List<Map>                                     │   │
│  │  │   └── {medicine, doseStrength, schedule, duration, conf}     │   │
│  │  ├── imageUrl: String (Firebase Storage path)                   │   │
│  │  ├── rawExtractionJson: String?                                 │   │
│  │  └── createdAt: Timestamp                                       │   │
│  │                                                                  │   │
│  │  appointments/{appointmentId}                                    │   │
│  │  ├── patientId, patientName, doctorId, doctorName               │   │
│  │  ├── specialization, dateTime, status, complaint                │   │
│  │  └── createdAt: Timestamp                                       │   │
│  │                                                                  │   │
│  │  reminders/{reminderId}                                          │   │
│  │  ├── patientId, prescriptionId, medicineName                    │   │
│  │  ├── schedule, reminderTimes, isActive                          │   │
│  │  └── createdAt: Timestamp                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  FIREBASE STORAGE (Images)                                       │   │
│  │  prescription_images/{userId}/{prescriptionId}.jpg               │   │
│  │  profile_images/{userId}.jpg                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  LOCAL CACHE: Room (SQLite) — optional, for offline             │   │
│  │  Firestore SDK already has built-in offline cache.              │   │
│  │  Room is extra for heavier offline needs.                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Entity Relationships:                                                  │
│                                                                         │
│  USERS ──1:N──▶ PRESCRIPTIONS ──1:N──▶ MEDICATIONS                     │
│    │                                         │                          │
│    └──1:N──▶ APPOINTMENTS                    └──1:N──▶ REMINDERS       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagrams

### Prescription Upload & Extraction Flow:

```
  ANDROID APP                    FASTAPI BACKEND           FIREBASE
  (Kotlin/Compose)               (Your Laptop)
      │                             │                         │
      │  1. User captures photo     │                         │
      │     using CameraX           │                         │
      │                             │                         │
      │  2. Convert to base64       │                         │
      │                             │                         │
      │  3. POST /extract-base64    │                         │
      │     via Retrofit2           │                         │
      │     {"image": "<base64>"}   │                         │
      │ ──────────────────────────▶ │                         │
      │                             │                         │
      │                             │  4. AI Pipeline:        │
      │                             │     Quality → YOLO →    │
      │                             │     OCR → Matching →    │
      │                             │     Spatial Grouping    │
      │                             │                         │
      │  5. JSON response           │                         │
      │     {medications: [...]}    │                         │
      │ ◀────────────────────────── │                         │
      │                             │                         │
      │  6. Show in bottom sheet    │                         │
      │     (editable by user)      │                         │
      │                             │                         │
      │  7. User taps "Save" →      │                         │
      │     Upload image to Storage ──────────────────────▶   │
      │     Save Rx to Firestore   ───────────────────────▶   │
      │                             │                         │
```

### Authentication Flow:

```
  ANDROID APP                    FIREBASE AUTH
      │                             │
      │  1. Email/password OR       │
      │     Google Sign-In          │
      │     (Firebase SDK)          │
      │ ──────────────────────────▶ │
      │                             │
      │  2. FirebaseUser returned   │
      │     (uid, email, token)     │
      │ ◀────────────────────────── │
      │                             │
      │  3. Check Firestore:        │
      │     users/{uid} exists?     │
      │                             │
      │  YES → Read userType →      │
      │     Navigate to Home        │
      │                             │
      │  NO → Show role picker →    │
      │     Save to Firestore →     │
      │     Navigate to Home        │
      │                             │
```

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DEVELOPMENT SETUP (Current)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Your Laptop (Backend — NVIDIA GTX 1660)                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • FastAPI + Uvicorn                    Port: 8000              │   │
│  │  • YOLOv8s + PaddleOCR (GPU)           CUDA 12.1               │   │
│  │  • Quality Checker (ResNet18)                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↕ HTTP (WiFi / same network)              │
│  Physical Android Device / Emulator                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • MediScan Kotlin app                                          │   │
│  │  • Emulator: http://10.0.2.2:8000                               │   │
│  │  • Physical: http://192.168.x.x:8000                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↕ HTTPS                                   │
│  Firebase (Cloud — Free Tier)                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  • Auth: unlimited email/Google users                           │   │
│  │  • Firestore: 1GB storage, 50K reads/day                       │   │
│  │  • Storage: 5GB, 1GB/day download                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 API Response Format

### POST /extract-base64 — Main extraction endpoint

**Request:** `{"image": "<base64_jpg_string>"}`

**Response (accepted):**
```json
{
  "prescription_id": "20260224_153000",
  "extraction_timestamp": "2026-02-24T15:30:00",
  "model_version": "v6_9class_english",
  "ocr_engine": "paddleocr",
  "status": "completed",
  "task_id": "a1b2c3d4",
  "medications": [
    {
      "medicine": "Napa Extra",
      "dose_strength": "500mg",
      "schedule": "3 times daily",
      "duration": "5 days",
      "confidence": { "medicine": 0.95, "dose_strength": 0.88, "schedule": 0.82, "duration": 0.79 }
    }
  ],
  "medication_count": 1,
  "doctor": { "name": "Dr. Ahmed", "hospital": "Dhaka Medical College" },
  "prescription_info": { "date": "14/01/2026", "diagnoses": ["Fever"], "tests": ["CBC"] },
  "quality_check": { "is_acceptable": true, "quality_score": 0.92, "issues": [] },
  "stats": { "total_fields_detected": 8, "medicines_found": 1 }
}
```

**Response (rejected):**
```json
{
  "status": "rejected",
  "message": "The image quality is poor. Please retake the photo.",
  "medications": [],
  "medication_count": 0,
  "quality_check": { "is_acceptable": false, "quality_score": 0.15 }
}
```

---

## 🔧 Complete Technology Stack

| Layer | Technology | Status |
|-------|------------|--------|
| **Android App** | Kotlin + Jetpack Compose (Material 3) | 🔜 To Build |
| **Auth** | Firebase Auth (email + Google Sign-In) | 🔜 To Integrate |
| **Cloud DB** | Firebase Firestore | 🔜 To Integrate |
| **Image Storage** | Firebase Storage | 🔜 To Integrate |
| **Local Cache** | Room (SQLite) | 🔜 Optional |
| **HTTP Client** | Retrofit2 + OkHttp | 🔜 To Build |
| **DI** | Hilt (Dagger) | 🔜 To Build |
| **Camera** | CameraX | 🔜 To Build |
| **Charts** | Vico | 🔜 To Build |
| **Maps** | Google Maps Compose | 🔜 To Build |
| **Notifications** | WorkManager + FCM | 🔜 To Build |
| **AI Backend** | FastAPI v6.1 | ✅ **Done** |
| **YOLO v6** | YOLOv8s (9 classes, 98.6% mAP50) | ✅ **Done** |
| **OCR** | PaddleOCR 3.2.2 (English) | ✅ **Done** |
| **Quality Checker** | ResNet18 + Laplacian (80%) | ✅ **Done** |

---

*Document Created: January 14, 2026*
*Last Updated: February 24, 2026 — Full rewrite: unified Firebase + Kotlin/Compose architecture*
*Project: MediScan - AI-Powered Prescription Digitization*
