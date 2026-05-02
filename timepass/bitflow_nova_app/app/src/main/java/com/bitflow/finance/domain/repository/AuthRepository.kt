package com.bitflow.finance.domain.repository

import com.bitflow.finance.data.local.entity.UserAccountEntity
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    val currentUser: Flow<String?>
    val isBitflowAdmin: Flow<Boolean>
    val currentUserId: Flow<String> // Unique identifier for data isolation
    
    suspend fun signup(
        username: String,
        displayName: String,
        password: String,
        securityQuestion: String,
        securityAnswer: String
    ): Result<UserAccountEntity>
    
    suspend fun login(username: String, password: String): Result<UserAccountEntity?>
    
    suspend fun verifySecurityQuestion(
        username: String,
        securityAnswer: String
    ): Result<UserAccountEntity>
    
    suspend fun loginWithAccount(account: UserAccountEntity): Result<Unit>
    
    suspend fun logout()
    
    suspend fun checkAuth(): Boolean
    
    suspend fun checkUsernameAvailable(username: String): Boolean
}
