package com.bitflow.finance.domain.repository

import kotlinx.coroutines.flow.Flow

import com.bitflow.finance.domain.model.AppMode

interface SettingsRepository {
    val currencySymbol: Flow<String>
    val isPrivacyModeEnabled: Flow<Boolean>
    val isBiometricEnabled: Flow<Boolean>
    val userName: Flow<String>
    val isOnboardingCompleted: Flow<Boolean>
    val appMode: Flow<AppMode>
    
    suspend fun setCurrencySymbol(symbol: String)
    suspend fun setPrivacyMode(enabled: Boolean)
    suspend fun setBiometricEnabled(enabled: Boolean)
    suspend fun setUserName(name: String)
    suspend fun setOnboardingCompleted(completed: Boolean)
    suspend fun setAppMode(mode: AppMode)
}
