# 📱 MediScan — Android App Development Specification

> **For AI Assistant (GitHub Copilot / Claude Opus 4.6):** This document contains the complete specification for building the MediScan Android application using **Kotlin & Jetpack Compose**. Read this entire document carefully, along with `SYSTEM_DESIGN.md` and `BACKEND_API_REFERENCE.md`, before starting development.

---

## 🎯 Project Overview

**App Name:** MediScan
**Platform:** Android (Kotlin + Jetpack Compose)
**IDE:** Android Studio (project opened in VS Code for AI-assisted development)
**Min SDK:** 26 (Android 8.0)
**Target SDK:** 34 (Android 14)
**Package Name:** `com.mediscan.app`
**Purpose:** AI-Powered Prescription Digitization & Smart Medicine Management
**Language Support:** English only (Bengali handwriting support planned for future)

### Key Features:
- Prescription scanning using AI (YOLO + PaddleOCR) via FastAPI backend
- Digital prescription storage (Firebase Firestore)
- Doctor appointment management
- Medicine browsing
- Nearby hospital finder (Google Maps)
- Multi-line diagnosis charts for doctors (Vico)
- Medication reminders (WorkManager)

---

## 🎨 Design Guidelines

### Color Palette:
```kotlin
// core/theme/Color.kt
val MediBlue = Color(0xFF2196F3)        // Primary
val HealthGreen = Color(0xFF4CAF50)     // Secondary / Success
val WarningOrange = Color(0xFFFF9800)   // Warning / Accent
val ErrorRed = Color(0xFFF44336)        // Error
val BackgroundGray = Color(0xFFF5F5F5)  // Background
val CardWhite = Color(0xFFFFFFFF)       // Card background
val TextPrimary = Color(0xFF212121)     // Primary text
val TextSecondary = Color(0xFF757575)   // Secondary text
```

### Typography:
```kotlin
// core/theme/Type.kt
// Headings: Poppins (Bold) — import via Google Fonts
// Body: Roboto (Regular) — default Material 3 font
```

### UI Requirements:
- **Material 3 Design** with dynamic color support
- Border radius: 16.dp for cards, 12.dp for buttons
- Elevation: 4.dp for cards
- Consistent padding: 16.dp
- Card-based UI components
- Gradient accents for headers
- Bottom sheet modals for forms
- Shimmer loading effects (accompanist or custom)
- Pull-to-refresh on lists

---

## 🏗️ Technical Architecture

### Tech Stack:
```yaml
Language: Kotlin 1.9+
UI Framework: Jetpack Compose (Material 3)
IDE: Android Studio (VS Code for AI dev)
Architecture: MVVM + Clean Architecture
Min SDK: 26 (Android 8.0)
Target SDK: 34 (Android 14)

# Core Libraries
DI: Hilt (Dagger) 2.50+
HTTP Client: Retrofit2 2.9+ with OkHttp 4.12+
Serialization: Gson or Kotlinx Serialization
Navigation: Navigation Compose 2.7+
Image Loading: Coil Compose 2.5+

# Firebase (all free tier)
Auth: Firebase Auth (email/password + Google Sign-In)
Database: Firebase Firestore
Storage: Firebase Storage
Push: Firebase Cloud Messaging (FCM)

# Local
Offline Cache: Room (SQLite) 2.6+
Token Storage: EncryptedSharedPreferences

# Features
Camera: CameraX 1.3+
Charts: Vico 2.0+ (Compose-native)
Maps: Google Maps Compose 4.3+
Reminders: WorkManager 2.9+
```

### build.gradle.kts (Module: app) — Key Dependencies:
```kotlin
dependencies {
    // Compose BOM
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.activity:activity-compose:1.8.2")

    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.7")

    // Hilt
    implementation("com.google.dagger:hilt-android:2.50")
    kapt("com.google.dagger:hilt-compiler:2.50")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")

    // Retrofit + OkHttp
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.7.2"))
    implementation("com.google.firebase:firebase-auth-ktx")
    implementation("com.google.firebase:firebase-firestore-ktx")
    implementation("com.google.firebase:firebase-storage-ktx")
    implementation("com.google.firebase:firebase-messaging-ktx")

    // Google Sign-In
    implementation("com.google.android.gms:play-services-auth:20.7.0")

    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")

    // CameraX
    implementation("androidx.camera:camera-camera2:1.3.1")
    implementation("androidx.camera:camera-lifecycle:1.3.1")
    implementation("androidx.camera:camera-view:1.3.1")

    // Coil (Image loading)
    implementation("io.coil-kt:coil-compose:2.5.0")

    // Vico (Charts)
    implementation("com.patrykandpatrick.vico:compose-m3:2.0.0-alpha.12")

    // Google Maps
    implementation("com.google.maps.android:maps-compose:4.3.0")
    implementation("com.google.android.gms:play-services-maps:18.2.0")
    implementation("com.google.android.gms:play-services-location:21.1.0")

    // WorkManager (reminders)
    implementation("androidx.work:work-runtime-ktx:2.9.0")

    // EncryptedSharedPreferences
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // Lifecycle
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")

    // Permissions
    implementation("com.google.accompanist:accompanist-permissions:0.34.0")
}
```

### Project Structure:
```
app/src/main/java/com/mediscan/
├── MediScanApp.kt                      # @HiltAndroidApp
├── MainActivity.kt                      # Single Activity (setContent { })
│
├── core/
│   ├── constants/
│   │   └── ApiEndpoints.kt             # FastAPI base URL
│   ├── theme/
│   │   ├── Theme.kt                    # MediScanTheme
│   │   ├── Color.kt                    # Color palette
│   │   └── Type.kt                     # Poppins + Roboto
│   ├── navigation/
│   │   └── NavGraph.kt                 # All routes
│   └── utils/
│       ├── Validators.kt               # Email/phone validators
│       └── NetworkResult.kt            # sealed class Success/Error/Loading
│
├── data/
│   ├── model/
│   │   ├── User.kt
│   │   ├── Prescription.kt
│   │   ├── Medication.kt
│   │   ├── Appointment.kt
│   │   └── ExtractionResult.kt         # Maps to FastAPI response
│   ├── remote/
│   │   └── FastApiService.kt           # Retrofit interface
│   ├── local/
│   │   ├── AppDatabase.kt              # Room
│   │   └── dao/
│   └── repository/
│       ├── AuthRepository.kt
│       ├── PrescriptionRepository.kt
│       ├── AppointmentRepository.kt
│       └── UserRepository.kt
│
├── di/
│   ├── AppModule.kt
│   ├── NetworkModule.kt
│   └── DatabaseModule.kt
│
├── ui/
│   ├── viewmodel/
│   │   ├── AuthViewModel.kt
│   │   ├── PrescriptionViewModel.kt
│   │   ├── ScanViewModel.kt
│   │   ├── AppointmentViewModel.kt
│   │   └── DoctorViewModel.kt
│   ├── screens/
│   │   ├── splash/SplashScreen.kt
│   │   ├── auth/LoginScreen.kt
│   │   ├── auth/SignUpScreen.kt
│   │   ├── patient/PatientMainScreen.kt
│   │   ├── patient/home/PatientHomeScreen.kt
│   │   ├── patient/scan/ScanScreen.kt
│   │   ├── patient/docs/DocsScreen.kt
│   │   ├── patient/profile/PatientProfileScreen.kt
│   │   ├── doctor/DoctorMainScreen.kt
│   │   ├── doctor/appointments/DoctorAppointmentsScreen.kt
│   │   ├── doctor/records/DoctorRecordsScreen.kt
│   │   └── doctor/profile/DoctorProfileScreen.kt
│   └── components/
│       ├── common/ (MediButton, MediTextField, LoadingIndicator, MediCard)
│       ├── PrescriptionCard.kt
│       ├── MedicationCard.kt
│       └── ExtractionResultSheet.kt
│
└── service/
    └── ReminderWorker.kt
```

---

## 📊 Data Models (Kotlin)

### User:
```kotlin
data class User(
    val id: String = "",                    // Firebase UID
    val email: String = "",
    val fullName: String = "",
    val phone: String = "",
    val profileImageUrl: String? = null,
    val userType: String = "patient",       // "patient" or "doctor"
    val createdAt: Long = System.currentTimeMillis(),

    // Patient-specific
    val dateOfBirth: String? = null,
    val bloodGroup: String? = null,
    val address: String? = null,
    val emergencyContact: String? = null,

    // Doctor-specific
    val licenseNumber: String? = null,
    val specialization: String? = null,
    val hospital: String? = null,
    val consultationFee: String? = null,
    val availableDays: List<String>? = null,
    val availableTimeRange: String? = null,
)
```

### Prescription:
```kotlin
data class Prescription(
    val id: String = "",
    val patientId: String = "",             // Firebase UID
    val doctorName: String? = null,
    val hospital: String? = null,
    val visitDate: Long = System.currentTimeMillis(),
    val diagnosis: String? = null,
    val medications: List<Medication> = emptyList(),
    val imageUrl: String? = null,           // Firebase Storage URL
    val rawExtractionJson: String? = null,  // Full API response (for debugging)
    val createdAt: Long = System.currentTimeMillis(),
)
```

### Medication:
```kotlin
data class Medication(
    val medicine: String = "",
    val doseStrength: String? = null,
    val schedule: String? = null,
    val duration: String? = null,
    val confidence: Double? = null,         // YOLO confidence (0.0-1.0)
)
```

### Appointment:
```kotlin
data class Appointment(
    val id: String = "",
    val patientId: String = "",
    val patientName: String = "",
    val doctorId: String = "",
    val doctorName: String = "",
    val specialization: String = "",
    val dateTime: Long = 0L,
    val status: String = "scheduled",       // "scheduled", "completed", "cancelled"
    val complaint: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
)
```

### ExtractionResult (FastAPI response):
```kotlin
data class ExtractionResult(
    @SerializedName("prescription_id") val prescriptionId: String = "",
    @SerializedName("extraction_timestamp") val extractionTimestamp: String = "",
    @SerializedName("model_version") val modelVersion: String = "",
    @SerializedName("ocr_engine") val ocrEngine: String = "",
    val status: String = "",
    @SerializedName("task_id") val taskId: String = "",
    val medications: List<ExtractedMedication> = emptyList(),
    @SerializedName("medication_count") val medicationCount: Int = 0,
    val doctor: DoctorInfo? = null,
    @SerializedName("prescription_info") val prescriptionInfo: PrescriptionInfo? = null,
    @SerializedName("quality_check") val qualityCheck: QualityCheck? = null,
    val message: String? = null,            // Present when status="rejected"
)

data class ExtractedMedication(
    val medicine: String? = null,
    @SerializedName("dose_strength") val doseStrength: String? = null,
    val schedule: String? = null,
    val duration: String? = null,
    val confidence: MedicationConfidence? = null,
)

data class MedicationConfidence(
    val medicine: Double? = null,
    @SerializedName("dose_strength") val doseStrength: Double? = null,
    val schedule: Double? = null,
    val duration: Double? = null,
)

data class DoctorInfo(
    val name: String? = null,
    val hospital: String? = null,
)

data class PrescriptionInfo(
    val date: String? = null,
    val diagnoses: List<String>? = null,
    val tests: List<String>? = null,
)

data class QualityCheck(
    @SerializedName("is_acceptable") val isAcceptable: Boolean = false,
    @SerializedName("quality_label") val qualityLabel: String = "",
    @SerializedName("quality_score") val qualityScore: Double = 0.0,
    val issues: List<String> = emptyList(),
    val recommendation: String? = null,
)

data class QualityCheckRequest(
    val image: String,                      // base64-encoded image
)
```

---

## 📱 Screen Specifications

---

### 1️⃣ SPLASH SCREEN

**File:** `ui/screens/splash/SplashScreen.kt`

**UI:**
- Full screen gradient background (MediBlue to light blue)
- Centered app logo (medical cross icon)
- "MediScan" text below logo (white, bold, Poppins)
- Tagline: "Your Smart Prescription Companion" (white, smaller)
- CircularProgressIndicator at bottom

**Logic:**
```
1. Display for 2 seconds
2. Check Firebase Auth state: auth.currentUser
3. If logged in:
   a. Read userType from Firestore users/{uid}
   b. If "patient" → PatientMainScreen
   c. If "doctor" → DoctorMainScreen
4. If not logged in → LoginScreen
5. Use fade transition via Navigation Compose
```

---

### 2️⃣ LOGIN SCREEN

**File:** `ui/screens/auth/LoginScreen.kt`

**UI Elements:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    [App Logo - small]                        │
│                                                             │
│                   "Welcome Back"                            │
│                "Sign in to continue"                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📧  Email                                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔒  Password                            [👁 toggle] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                              "Forgot Password?" (link)     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              🔵  Login  (full width)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│                    ─── OR ───                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [G]  Continue with Google  (outlined)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│         "Don't have an account? Sign Up" (link)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Logic:**
- Validate email format and password ≥ 6 chars
- Show CircularProgressIndicator in button when loading
- `auth.signInWithEmailAndPassword(email, password)`
- Google Sign-In: `auth.signInWithCredential(googleCredential)`
- On success → check Firestore for userType → navigate
- On error → show Snackbar with error message
- "Forgot Password?" → `auth.sendPasswordResetEmail(email)`

---

### 3️⃣ SIGN UP SCREEN

**File:** `ui/screens/auth/SignUpScreen.kt`

**UI Elements:**
```
┌─────────────────────────────────────────────────────────────┐
│                    [App Logo]                                │
│                                                             │
│                  "Create Account"                           │
│               "Join MediScan today"                         │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │  👤  Full Name                                    │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  📧  Email                                        │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  📱  Phone Number                                 │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  🔒  Password                         [👁 toggle] │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  🔒  Confirm Password                 [👁 toggle] │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
│  I am a:  (● Patient)  (○ Doctor)                          │
│                                                             │
│  ── If Doctor selected: ──                                  │
│  ┌──────────────────────────────────────────────────┐      │
│  │  📋  Medical License Number                       │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  🏥  Specialization (dropdown)                    │      │
│  └──────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────┐      │
│  │  🏥  Hospital/Clinic Name                         │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │              🔵  Sign Up  (full width)             │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │  [G]  Continue with Google  (outlined)            │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
│       "Already have an account? Login" (link)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Logic:**
1. Validate all fields (name not empty, email valid, passwords match, ≥6 chars)
2. `auth.createUserWithEmailAndPassword(email, password)`
3. On success → save user profile to Firestore `users/{uid}`:
   ```kotlin
   val user = User(
       id = auth.currentUser!!.uid,
       email = email,
       fullName = name,
       phone = phone,
       userType = if (isDoctor) "doctor" else "patient",
       // doctor fields if applicable
   )
   firestore.collection("users").document(user.id).set(user)
   ```
4. Navigate to PatientMainScreen or DoctorMainScreen based on role
5. Google Sign-In: same flow, but auto-fill name/email from Google account. Show role picker dialog after Google auth.

---

## 👤 PATIENT PORTAL

### 4️⃣ PATIENT MAIN SCREEN (Bottom Navigation)

**File:** `ui/screens/patient/PatientMainScreen.kt`

**Bottom Navigation (4 tabs):**
1. **Home** — Home icon
2. **Scan** — Camera icon
3. **Docs** — Document icon
4. **Profile** — Person icon

Active: MediBlue fill, Label shown. Inactive: Gray outline.

---

### 5️⃣ PATIENT HOME SCREEN

**File:** `ui/screens/patient/home/PatientHomeScreen.kt`

**Sections (scrollable Column):**

**Header:** "Good Morning, {userName}" + profile avatar (right) + notification bell

**Section 1 — Upcoming Appointments (LazyRow):**
- Horizontal scrollable appointment cards
- Each card: doctor name, specialization, date/time, [View] [Cancel] buttons
- If empty: "No Appointments Yet" + [Book Now] button

**Section 2 — Book Appointment Card:**
- Gradient blue card with medical illustration
- "Book an Appointment" title
- "Find and book appointments with top doctors near you"
- On tap → Doctor Search Screen (list of doctors, search, filter by specialization, book with time picker)

**Section 3 — Buy Medicines Card:**
- Gradient green card
- "Buy Medicines" + "Order medicines delivered to your doorstep"
- On tap → Medicine List Screen (search, categories, medicine cards with name/generic/price)

**Section 4 — Nearby Hospitals Card:**
- Map preview card
- "Nearby Hospitals" + "Find hospitals and clinics around your location"
- On tap → Google Maps screen with hospital markers (current location + nearby hospitals from Places API)

---

### 6️⃣ SCAN SCREEN (Core AI Feature)

**File:** `ui/screens/patient/scan/ScanScreen.kt`

**Initial State:**
```
┌─────────────────────────────────────────────────────────────┐
│                     📸 Scan Prescription                    │
│                                                             │
│              Take a photo of your prescription              │
│              and let AI extract the details                 │
│                                                             │
│                         ┌───────┐                           │
│                         │       │                           │
│                         │   +   │  (Large circular FAB)     │
│                         │       │                           │
│                         └───────┘                           │
│                                                             │
│                    Tap to scan prescription                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  💡 Tips for best results:                           │   │
│  │  • Ensure good lighting                              │   │
│  │  • Keep prescription flat                            │   │
│  │  • Capture entire prescription in frame              │   │
│  │  • Avoid shadows and glare                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Flow on tap:**
1. Request camera permission (Accompanist Permissions)
2. Open CameraX preview (full screen)
3. User captures photo → get `ImageProxy` → convert to byte array
4. Show loading: "Analyzing prescription..." with progress indicator
5. Convert image to base64
6. **Call FastAPI:** `POST /extract-base64` via Retrofit2 with `{"image": base64String}`
7. Parse `ExtractionResult` response
8. If `status == "rejected"` → show error with quality message, offer to retake
9. If `status == "completed"` → show Extraction Result Bottom Sheet

**Extraction Result Bottom Sheet:**
```
┌─────────────────────────────────────────────────────────────┐
│  ─────────────────  (drag handle)                           │
│                                                             │
│           ✅ Prescription Scanned Successfully              │
│                                                             │
│  👨‍⚕️ Doctor Information                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Doctor Name    │ [editable field]                  │    │
│  │ Hospital       │ [editable field]                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  📅 Visit Date                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Date           │ [editable / date picker]          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  💊 Medications (Editable)                                  │
│                                                             │
│  Medicine 1:                                                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Name: [editable] │  │ Strength: [edit] │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Schedule: [edit]  │  │ Duration: [edit] │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
│  [+ Add Another Medicine]                                   │
│                                                             │
│  ┌─────────────────┐  ┌────────────────────────┐           │
│  │     Cancel      │  │  💾 Save Prescription  │           │
│  └─────────────────┘  └────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

**On Save:**
1. Upload original image to Firebase Storage: `prescription_images/{uid}/{rxId}.jpg`
2. Create Prescription object with medications
3. Save to Firestore: `prescriptions/{rxId}`
4. Show success Snackbar
5. Navigate to Docs screen (updated list)

---

### 7️⃣ DOCS SCREEN (Prescription History)

**File:** `ui/screens/patient/docs/DocsScreen.kt`

**UI:**
- Header: "My Prescriptions" + search icon
- Filter row: [All ▼] [This Month ▼] [Sort by Date ▼]
- LazyColumn of PrescriptionCard items:
  - Date, doctor name, hospital
  - Medication summary (first 2 medicines shown)
  - [View Details] button + [🗑️ Delete] icon button
- Empty state: "No Prescriptions Yet" + "Go to Scan" button

**Prescription Detail Screen (on "View Details"):**
- Full prescription view with all medications
- Original scanned image (Coil, tappable for full-screen)
- Edit button (modify medications)
- Share button (future: generate PDF)
- Delete with confirmation dialog

---

### 8️⃣ PATIENT PROFILE SCREEN

**File:** `ui/screens/patient/profile/PatientProfileScreen.kt`

**UI:**
- Circular profile image with edit overlay
- Name + email display
- Menu items (each navigates to sub-screen):
  - 👤 Edit Profile
  - 🔔 Notification Settings
  - 🔒 Change Password
  - 📋 Medical History
  - ❓ Help & Support
  - 📄 Terms & Privacy Policy
  - 🚪 Logout

**Edit Profile:** name, phone, DOB, blood group, address, emergency contact, profile photo picker

**Logout:** `auth.signOut()` → navigate to LoginScreen, clear back stack

---

## 👨‍⚕️ DOCTOR PORTAL

### 9️⃣ DOCTOR MAIN SCREEN (Bottom Navigation)

**File:** `ui/screens/doctor/DoctorMainScreen.kt`

**Bottom Navigation (3 tabs):**
1. **Appointments** — Calendar icon
2. **Records** — Chart/analytics icon
3. **Profile** — Person icon

---

### 🔟 DOCTOR APPOINTMENTS SCREEN

**File:** `ui/screens/doctor/appointments/DoctorAppointmentsScreen.kt`

**UI:**
- Header: "Appointments" + date filter dropdown
- LazyColumn of appointment cards:
  - Time slot, patient name, age/gender
  - Phone number, complaint text
  - [View History] [Start Consultation] [Cancel] buttons
- Empty state: "No Appointments Today"

**View History:** Shows patient's past prescriptions and diagnoses from Firestore
**Start Consultation:** Opens form → add diagnosis, write prescription manually, save to Firestore

---

### 1️⃣1️⃣ DOCTOR RECORDS SCREEN (Analytics)

**File:** `ui/screens/doctor/records/DoctorRecordsScreen.kt`

**UI:**
- Overview cards row: Total Patients, Today, This Week, Pending
- **Diagnosis Trends Chart (Vico):** Multi-line chart, X=months, Y=case count, color-coded by diagnosis
- Patient search bar
- Recent patients list with [View →] button

**Chart:** Use Vico `CartesianChartHost` with `LineCartesianLayer`, multiple data series for different diagnoses

---

### 1️⃣2️⃣ DOCTOR PROFILE SCREEN

**File:** `ui/screens/doctor/profile/DoctorProfileScreen.kt`

**Same as Patient Profile plus:**
- 🏥 Hospital/Clinic Details
- ⏰ Available Timings
- 💰 Consultation Fee

---

## 🔌 API Integration (Retrofit2)

### FastApiService.kt:
```kotlin
interface FastApiService {

    @POST("check-quality-base64")
    suspend fun checkQuality(
        @Body request: QualityCheckRequest
    ): QualityCheck

    @POST("extract-base64")
    suspend fun extractPrescription(
        @Body request: QualityCheckRequest  // same format: {"image": "base64..."}
    ): ExtractionResult

    @GET("health")
    suspend fun healthCheck(): Map<String, Any>
}
```

### NetworkModule.kt (Hilt):
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    // ⚠️ Change this based on your setup:
    // Emulator: "http://10.0.2.2:8000/"
    // Physical device (same WiFi): "http://192.168.x.x:8000/"
    private const val BASE_URL = "http://10.0.2.2:8000/"

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)  // AI processing takes time
            .writeTimeout(60, TimeUnit.SECONDS)
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideFastApiService(retrofit: Retrofit): FastApiService {
        return retrofit.create(FastApiService::class.java)
    }
}
```

### How to use in ViewModel:
```kotlin
@HiltViewModel
class ScanViewModel @Inject constructor(
    private val fastApiService: FastApiService,
    private val prescriptionRepo: PrescriptionRepository,
) : ViewModel() {

    private val _extractionState = MutableStateFlow<NetworkResult<ExtractionResult>>(NetworkResult.Idle)
    val extractionState: StateFlow<NetworkResult<ExtractionResult>> = _extractionState

    fun extractPrescription(imageBytes: ByteArray) {
        viewModelScope.launch {
            _extractionState.value = NetworkResult.Loading

            try {
                val base64 = Base64.encodeToString(imageBytes, Base64.NO_WRAP)
                val request = QualityCheckRequest(image = base64)
                val result = fastApiService.extractPrescription(request)

                if (result.status == "rejected") {
                    _extractionState.value = NetworkResult.Error(
                        result.message ?: "Image quality too poor"
                    )
                } else {
                    _extractionState.value = NetworkResult.Success(result)
                }
            } catch (e: Exception) {
                _extractionState.value = NetworkResult.Error(
                    "Cannot connect to server: ${e.localizedMessage}"
                )
            }
        }
    }
}
```

---

## 🔥 Firebase Configuration

### What the developer needs to do manually:
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project "MediScan"
3. Add Android app with package `com.mediscan.app`
4. Download `google-services.json` → put in `app/` folder
5. Enable Authentication → Email/Password + Google provider
6. Create Firestore database (test mode initially)
7. Create Storage bucket (test mode initially)
8. Add SHA-1 fingerprint for Google Sign-In (from `./gradlew signingReport`)

### Firestore Security Rules (production):
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own document
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      // Doctors can be read by any authenticated user (for search)
      allow read: if request.auth != null;
    }
    
    // Prescriptions: owner can CRUD, linked doctor can read
    match /prescriptions/{rxId} {
      allow create: if request.auth != null;
      allow read, update, delete: if request.auth != null 
        && resource.data.patientId == request.auth.uid;
    }
    
    // Appointments: both patient and doctor can access
    match /appointments/{apptId} {
      allow create: if request.auth != null;
      allow read, update, delete: if request.auth != null 
        && (resource.data.patientId == request.auth.uid 
            || resource.data.doctorId == request.auth.uid);
    }
    
    // Reminders: owner only
    match /reminders/{remId} {
      allow read, write: if request.auth != null 
        && resource.data.patientId == request.auth.uid;
    }
  }
}
```

### Firebase Storage Rules:
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /prescription_images/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /profile_images/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

---

## 🔌 Network Configuration

### AndroidManifest.xml additions:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

<application
    android:usesCleartextTraffic="true"
    ... >
    
    <!-- Google Maps API Key -->
    <meta-data
        android:name="com.google.android.geo.API_KEY"
        android:value="YOUR_MAPS_API_KEY" />
</application>
```

### Connection URLs:

| Environment | FastAPI URL | Notes |
|-------------|-------------|-------|
| **Android Emulator** | `http://10.0.2.2:8000/` | 10.0.2.2 = host machine |
| **Physical Device** | `http://192.168.x.x:8000/` | Your PC's local WiFi IP |
| **Production** | `https://api.mediscan.com/` | Future: deployed with HTTPS |

---

## 🚀 Development Order

Build the app in this exact order:

| Phase | What to Build | Test Checkpoint |
|-------|--------------|-----------------|
| **1** | Project setup + Hilt + Theme + Navigation shell | App launches, shows blank screen |
| **2** | Splash → Login → SignUp screens + Firebase Auth | Can register & login with email + Google |
| **3** | Patient bottom nav + Home screen (static UI) | Tab navigation works |
| **4** | Scan screen + CameraX + Retrofit → FastAPI | Can scan Rx and see extracted medications |
| **5** | Save prescriptions to Firestore + Docs screen | Prescriptions persist and list correctly |
| **6** | Patient Profile + Edit Profile | Profile read/write works |
| **7** | Doctor portal: Appointments + Records + Profile | Doctor role has full dashboard |
| **8** | Appointments system (patient books, doctor sees) | Booking flow works end-to-end |
| **9** | Google Maps integration | Hospital finder works |
| **10** | Medication reminders (WorkManager) | Notifications fire at correct times |
| **11** | Polish: loading states, error handling, animations | Production-quality UX |

---

## 📝 Notes for Future Development

1. **Bengali Handwriting Support** — Deferred to future version
2. **Offline Mode** — Firestore SDK has built-in offline cache; Room for extra persistence
3. **Drug Interaction Warnings** — Alert users about potential drug interactions
4. **Telemedicine** — Video consultation feature
5. **PDF Export** — Generate prescription PDFs

---

*Document Created: January 14, 2026*
*Last Updated: February 24, 2026 — Full rewrite: Kotlin/Compose, removed all Flutter/Dart, unified Firebase*
*App Name: MediScan*
*Version: 2.0.0*
