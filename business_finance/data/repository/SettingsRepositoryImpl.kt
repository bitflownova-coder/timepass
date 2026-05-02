package com.bitflow.finance.data.repository

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.bitflow.finance.domain.repository.SettingsRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import com.bitflow.finance.domain.model.AppMode
import javax.inject.Inject
import javax.inject.Singleton

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

@Singleton
class SettingsRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context
) : SettingsRepository {

    private val CURRENCY_KEY = stringPreferencesKey("currency_symbol")
    private val PRIVACY_MODE_KEY = booleanPreferencesKey("privacy_mode")
    private val BIOMETRIC_ENABLED_KEY = booleanPreferencesKey("biometric_enabled")
    private val USER_NAME_KEY = stringPreferencesKey("user_name")
    private val ONBOARDING_COMPLETED_KEY = booleanPreferencesKey("onboarding_completed")
    private val APP_MODE_KEY = stringPreferencesKey("app_mode")

    override val currencySymbol: Flow<String> = context.dataStore.data
        .map { preferences ->
            preferences[CURRENCY_KEY] ?: "₹"
        }

    override val isPrivacyModeEnabled: Flow<Boolean> = context.dataStore.data
        .map { preferences ->
            preferences[PRIVACY_MODE_KEY] ?: false
        }

    override val isBiometricEnabled: Flow<Boolean> = context.dataStore.data
        .map { preferences ->
            preferences[BIOMETRIC_ENABLED_KEY] ?: false
        }

    override val userName: Flow<String> = context.dataStore.data
        .map { preferences ->
            preferences[USER_NAME_KEY] ?: ""
        }

    override val isOnboardingCompleted: Flow<Boolean> = context.dataStore.data
        .map { preferences ->
            preferences[ONBOARDING_COMPLETED_KEY] ?: false
        }

    override val appMode: Flow<AppMode> = context.dataStore.data
        .map { preferences ->
            val modeStr = preferences[APP_MODE_KEY] ?: AppMode.PERSONAL.name
            try {
                AppMode.valueOf(modeStr)
            } catch (e: Exception) {
                AppMode.PERSONAL
            }
        }

    override suspend fun setCurrencySymbol(symbol: String) {
        context.dataStore.edit { preferences ->
            preferences[CURRENCY_KEY] = symbol
        }
    }

    override suspend fun setPrivacyMode(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[PRIVACY_MODE_KEY] = enabled
        }
    }

    override suspend fun setBiometricEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[BIOMETRIC_ENABLED_KEY] = enabled
        }
    }

    override suspend fun setUserName(name: String) {
        context.dataStore.edit { preferences ->
            preferences[USER_NAME_KEY] = name
        }
    }

    override suspend fun setOnboardingCompleted(completed: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[ONBOARDING_COMPLETED_KEY] = completed
        }
    }


    override suspend fun setAppMode(mode: AppMode) {
        context.dataStore.edit { preferences ->
            preferences[APP_MODE_KEY] = mode.name
        }
    }
}
