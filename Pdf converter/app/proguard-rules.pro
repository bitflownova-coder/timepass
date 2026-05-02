# Add project specific ProGuard rules here.

# ─── PdfBox-Android ──────────────────────────────────────────────────────────
-keep class com.tom_roush.pdfbox.** { *; }
-dontwarn com.tom_roush.pdfbox.**

# ─── ML Kit ──────────────────────────────────────────────────────────────────
-keep class com.google.mlkit.** { *; }
-dontwarn com.google.mlkit.**

# ─── ZXing ───────────────────────────────────────────────────────────────────
-keep class com.google.zxing.** { *; }
-dontwarn com.google.zxing.**

# ─── Google Drive API ────────────────────────────────────────────────────────
-keep class com.google.api.** { *; }
-dontwarn com.google.api.**

# ─── Kotlin Coroutines ───────────────────────────────────────────────────────
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-keepclassmembers class kotlinx.coroutines.** { volatile <fields>; }

# ─── Room ────────────────────────────────────────────────────────────────────
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-dontwarn androidx.room.paging.**

# ─── Hilt ────────────────────────────────────────────────────────────────────
-keep class dagger.hilt.** { *; }
-keep class javax.inject.** { *; }
-dontwarn dagger.hilt.**

# ─── Compose ─────────────────────────────────────────────────────────────────
-dontwarn androidx.compose.**

# ─── Keep app data classes ───────────────────────────────────────────────────
-keep class com.bitflow.pdfconverter.core.domain.model.** { *; }
-keepclassmembers class com.bitflow.pdfconverter.core.data.database.entity.** { *; }
