package com.bitflow.pdfconverter.ui

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Environment
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.DarkMode
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.ImageSearch
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.LightMode
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.SettingsBrightness
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.edit

private const val PREFS_NAME = "pdf_converter_settings"
private const val KEY_THEME_MODE = "theme_mode"
private const val KEY_DYNAMIC_COLOR = "dynamic_color"
private const val KEY_NOTIFICATIONS = "notifications_enabled"
private const val KEY_SCAN_DPI = "scan_dpi"
private const val KEY_JPEG_QUALITY = "jpeg_quality"
private const val KEY_LANGUAGE = "language"
private const val KEY_OUTPUT_PATH = "output_path"

enum class ThemeMode(val label: String) {
    SYSTEM("System Default"),
    LIGHT("Light"),
    DARK("Dark")
}

// Thin wrapper around SharedPreferences for settings persistence
class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var themeMode: ThemeMode
        get() = try {
            ThemeMode.valueOf(prefs.getString(KEY_THEME_MODE, ThemeMode.SYSTEM.name) ?: ThemeMode.SYSTEM.name)
        } catch (_: Exception) { ThemeMode.SYSTEM }
        set(v) = prefs.edit { putString(KEY_THEME_MODE, v.name) }

    var dynamicColor: Boolean
        get() = prefs.getBoolean(KEY_DYNAMIC_COLOR, false)
        set(v) = prefs.edit { putBoolean(KEY_DYNAMIC_COLOR, v) }

    var notificationsEnabled: Boolean
        get() = prefs.getBoolean(KEY_NOTIFICATIONS, true)
        set(v) = prefs.edit { putBoolean(KEY_NOTIFICATIONS, v) }

    var scanDpi: Float
        get() = prefs.getFloat(KEY_SCAN_DPI, 150f)
        set(v) = prefs.edit { putFloat(KEY_SCAN_DPI, v) }

    var jpegQuality: Float
        get() = prefs.getFloat(KEY_JPEG_QUALITY, 85f)
        set(v) = prefs.edit { putFloat(KEY_JPEG_QUALITY, v) }

    var language: String
        get() = prefs.getString(KEY_LANGUAGE, "System Default") ?: "System Default"
        set(v) = prefs.edit { putString(KEY_LANGUAGE, v) }

    var outputPath: String
        get() = prefs.getString(KEY_OUTPUT_PATH, "") ?: ""
        set(v) = prefs.edit { putString(KEY_OUTPUT_PATH, v) }

    fun registerListener(listener: android.content.SharedPreferences.OnSharedPreferenceChangeListener) {
        prefs.registerOnSharedPreferenceChangeListener(listener)
    }

    fun unregisterListener(listener: android.content.SharedPreferences.OnSharedPreferenceChangeListener) {
        prefs.unregisterOnSharedPreferenceChangeListener(listener)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(onNavigateBack: () -> Unit) {
    val context = LocalContext.current
    val store = remember { SettingsStore(context) }

    var themeMode by remember { mutableStateOf(store.themeMode) }
    var dynamicColor by remember { mutableStateOf(store.dynamicColor) }
    var notificationsEnabled by remember { mutableStateOf(store.notificationsEnabled) }
    var scanDpi by remember { mutableFloatStateOf(store.scanDpi) }
    var jpegQuality by remember { mutableFloatStateOf(store.jpegQuality) }
    var language by remember { mutableStateOf(store.language) }
    var outputPath by remember { mutableStateOf(store.outputPath.ifBlank { "Documents/PdfConverter" }) }

    var showLanguageDialog by remember { mutableStateOf(false) }

    val folderPickerLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocumentTree()
    ) { uri: Uri? ->
        if (uri != null) {
            context.contentResolver.takePersistableUriPermission(
                uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )
            outputPath = uri.lastPathSegment ?: uri.toString()
            store.outputPath = uri.toString()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
        ) {
            // ── Appearance ──────────────────────────────────────────────────
            SettingsSectionHeader("Appearance")

            ThemeMode.entries.forEach { mode ->
                ListItem(
                    headlineContent = { Text(mode.label) },
                    leadingContent = {
                        Icon(
                            when (mode) {
                                ThemeMode.SYSTEM -> Icons.Default.SettingsBrightness
                                ThemeMode.LIGHT -> Icons.Default.LightMode
                                ThemeMode.DARK -> Icons.Default.DarkMode
                            },
                            contentDescription = null
                        )
                    },
                    trailingContent = {
                        RadioButton(
                            selected = themeMode == mode,
                            onClick = { themeMode = mode; store.themeMode = mode }
                        )
                    },
                    modifier = Modifier.clickable { themeMode = mode; store.themeMode = mode }
                )
            }

            ListItem(
                headlineContent = { Text("Dynamic Color") },
                supportingContent = { Text("Follow wallpaper colors (Android 12+)") },
                leadingContent = { Icon(Icons.Default.Tune, contentDescription = null) },
                trailingContent = {
                    Switch(
                        checked = dynamicColor,
                        onCheckedChange = { dynamicColor = it; store.dynamicColor = it }
                    )
                }
            )

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

            // ── Notifications ───────────────────────────────────────────────
            SettingsSectionHeader("Notifications")

            ListItem(
                headlineContent = { Text("Enable Notifications") },
                supportingContent = { Text("Get notified when tasks complete") },
                leadingContent = { Icon(Icons.Default.Notifications, contentDescription = null) },
                trailingContent = {
                    Switch(
                        checked = notificationsEnabled,
                        onCheckedChange = { notificationsEnabled = it; store.notificationsEnabled = it }
                    )
                }
            )

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

            // ── Language ────────────────────────────────────────────────────
            SettingsSectionHeader("Language")

            ListItem(
                headlineContent = { Text("App Language") },
                supportingContent = { Text(language) },
                leadingContent = { Icon(Icons.Default.Language, contentDescription = null) },
                modifier = Modifier.clickable { showLanguageDialog = true }
            )

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

            // ── Scanning ────────────────────────────────────────────────────
            SettingsSectionHeader("Scanning & Output Quality")

            ListItem(
                headlineContent = { Text("Scan DPI: ${scanDpi.toInt()}") },
                supportingContent = {
                    Column {
                        Text("Higher DPI = sharper scans, larger files")
                        Slider(
                            value = scanDpi,
                            onValueChange = { scanDpi = it },
                            onValueChangeFinished = { store.scanDpi = scanDpi },
                            valueRange = 72f..300f,
                            steps = 5
                        )
                    }
                },
                leadingContent = { Icon(Icons.Default.ImageSearch, contentDescription = null) }
            )

            ListItem(
                headlineContent = { Text("JPEG Quality: ${jpegQuality.toInt()}%") },
                supportingContent = {
                    Column {
                        Text("Quality used when compressing PDF images")
                        Slider(
                            value = jpegQuality,
                            onValueChange = { jpegQuality = it },
                            onValueChangeFinished = { store.jpegQuality = jpegQuality },
                            valueRange = 50f..100f,
                            steps = 9
                        )
                    }
                },
                leadingContent = { Icon(Icons.Default.Tune, contentDescription = null) }
            )

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

            // ── Storage ─────────────────────────────────────────────────────
            SettingsSectionHeader("Storage")

            ListItem(
                headlineContent = { Text("Output Folder") },
                supportingContent = { Text(outputPath) },
                leadingContent = { Icon(Icons.Default.Folder, contentDescription = null) },
                modifier = Modifier.clickable {
                    folderPickerLauncher.launch(
                        Uri.fromFile(
                            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS)
                        )
                    )
                }
            )

            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))

            // ── About ───────────────────────────────────────────────────────
            SettingsSectionHeader("About")

            ListItem(
                headlineContent = { Text("Version") },
                supportingContent = { Text("1.0.0") },
                leadingContent = { Icon(Icons.Default.Info, contentDescription = null) }
            )

            Spacer(modifier = Modifier.height(24.dp))
        }
    }

    if (showLanguageDialog) {
        LanguagePickerDialog(
            current = language,
            onSelect = { selected ->
                language = selected
                store.language = selected
                showLanguageDialog = false
            },
            onDismiss = { showLanguageDialog = false }
        )
    }
}

@Composable
private fun SettingsSectionHeader(title: String) {
    Text(
        text = title,
        style = MaterialTheme.typography.labelMedium,
        color = MaterialTheme.colorScheme.primary,
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
    )
}

@Composable
private fun LanguagePickerDialog(
    current: String,
    onSelect: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val options = listOf("System Default", "English", "Spanish", "French", "German", "Arabic", "Hindi", "Chinese")

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Select Language") },
        text = {
            Column {
                options.forEach { option ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelect(option) }
                            .padding(vertical = 4.dp)
                    ) {
                        RadioButton(selected = option == current, onClick = { onSelect(option) })
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(option)
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}
