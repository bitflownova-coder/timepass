package com.bitflow.finance.util

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Manages a secondary "decoy" PIN that shows an empty/fake state when used.
 * This provides plausible deniability for sensitive financial data.
 */
class DecoyPinManager(context: Context) {
    
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        "decoy_pin_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    companion object {
        private const val KEY_DECOY_PIN = "decoy_pin"
        private const val KEY_DECOY_ENABLED = "decoy_enabled"
        private const val KEY_DECOY_ACTIVE = "decoy_mode_active"
    }
    
    /**
     * Sets the decoy PIN.
     */
    fun setDecoyPin(pin: String) {
        prefs.edit()
            .putString(KEY_DECOY_PIN, pin)
            .putBoolean(KEY_DECOY_ENABLED, true)
            .apply()
    }
    
    /**
     * Removes the decoy PIN.
     */
    fun removeDecoyPin() {
        prefs.edit()
            .remove(KEY_DECOY_PIN)
            .putBoolean(KEY_DECOY_ENABLED, false)
            .putBoolean(KEY_DECOY_ACTIVE, false)
            .apply()
    }
    
    /**
     * Checks if decoy PIN feature is enabled.
     */
    fun isDecoyEnabled(): Boolean = prefs.getBoolean(KEY_DECOY_ENABLED, false)
    
    /**
     * Checks if the provided PIN matches the decoy PIN.
     */
    fun isDecoyPin(pin: String): Boolean {
        val decoyPin = prefs.getString(KEY_DECOY_PIN, null)
        return decoyPin != null && decoyPin == pin
    }
    
    /**
     * Activates decoy mode (shows fake empty state).
     */
    fun activateDecoyMode() {
        prefs.edit().putBoolean(KEY_DECOY_ACTIVE, true).apply()
    }
    
    /**
     * Deactivates decoy mode (shows real data).
     */
    fun deactivateDecoyMode() {
        prefs.edit().putBoolean(KEY_DECOY_ACTIVE, false).apply()
    }
    
    /**
     * Returns whether the app is currently in decoy mode.
     */
    fun isDecoyModeActive(): Boolean = prefs.getBoolean(KEY_DECOY_ACTIVE, false)
}
