package com.bitflow.pdfconverter

import android.content.SharedPreferences
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.edit
import com.bitflow.pdfconverter.core.ui.theme.PdfConverterTheme
import com.bitflow.pdfconverter.navigation.AppNavGraph
import com.bitflow.pdfconverter.navigation.Screen
import com.bitflow.pdfconverter.ui.SettingsStore
import com.bitflow.pdfconverter.ui.ThemeMode
import dagger.hilt.android.AndroidEntryPoint

private const val PREFS_MAIN = "main_prefs"
private const val KEY_ONBOARDING_DONE = "onboarding_done"
private const val KEY_USER_NAME = "user_name"
private const val KEY_USER_ROLE = "user_role"

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    private var themeMode by mutableStateOf(ThemeMode.SYSTEM)
    private var dynamicColor by mutableStateOf(false)

    private lateinit var settingsStore: SettingsStore

    private val prefListener = SharedPreferences.OnSharedPreferenceChangeListener { _, _ ->
        themeMode = settingsStore.themeMode
        dynamicColor = settingsStore.dynamicColor
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        settingsStore = SettingsStore(this)
        themeMode = settingsStore.themeMode
        dynamicColor = settingsStore.dynamicColor
        settingsStore.registerListener(prefListener)

        val prefs = getSharedPreferences(PREFS_MAIN, MODE_PRIVATE)
        val onboardingDone = prefs.getBoolean(KEY_ONBOARDING_DONE, false)

        val startDestination = if (onboardingDone) {
            Screen.Home.route
        } else {
            prefs.edit { putBoolean(KEY_ONBOARDING_DONE, true) }
            Screen.Onboarding.route
        }

        setContent {
            val darkTheme = when (themeMode) {
                ThemeMode.LIGHT -> false
                ThemeMode.DARK -> true
                ThemeMode.SYSTEM -> isSystemInDarkTheme()
            }
            PdfConverterTheme(darkTheme = darkTheme, dynamicColor = dynamicColor) {
                AppNavGraph(
                    startDestination = startDestination,
                    onProfileSaved = { name, role ->
                        prefs.edit {
                            putString(KEY_USER_NAME, name)
                            putString(KEY_USER_ROLE, role)
                        }
                    }
                )
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        settingsStore.unregisterListener(prefListener)
    }
}
