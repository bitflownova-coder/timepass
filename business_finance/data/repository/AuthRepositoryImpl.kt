package com.bitflow.finance.data.repository

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.bitflow.finance.data.local.dao.UserAccountDao
import com.bitflow.finance.data.local.entity.UserAccountEntity
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val userAccountDao: UserAccountDao
) : AuthRepository {

    // Thread-safe state for reactive session data
    private val _currentUserId = MutableStateFlow("default_user")
    private val _displayName = MutableStateFlow<String?>(null)
    private val _isLoggedIn = MutableStateFlow(false)
    private val _isAdmin = MutableStateFlow(false)

    // Encrypted SharedPreferences for session persistence
    private val encryptedPrefs: SharedPreferences by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context,
            "auth_prefs_encrypted",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    private companion object {
        const val PREF_USER_ID = "auth_user_id"
        const val PREF_DISPLAY_NAME = "auth_display_name"
        const val PREF_IS_LOGGED_IN = "auth_is_logged_in"
        const val PREF_IS_ADMIN = "auth_is_admin"
        const val SALT_LENGTH = 16 // 128 bits
    }

    init {
        // Load session from encrypted storage on init
        loadSessionFromStorage()
    }

    private fun loadSessionFromStorage() {
        _isLoggedIn.value = encryptedPrefs.getBoolean(PREF_IS_LOGGED_IN, false)
        _isAdmin.value = encryptedPrefs.getBoolean(PREF_IS_ADMIN, false)
        _currentUserId.value = encryptedPrefs.getString(PREF_USER_ID, "default_user") ?: "default_user"
        _displayName.value = encryptedPrefs.getString(PREF_DISPLAY_NAME, null)
    }

    private fun saveSessionToStorage() {
        encryptedPrefs.edit().apply {
            putBoolean(PREF_IS_LOGGED_IN, _isLoggedIn.value)
            putBoolean(PREF_IS_ADMIN, _isAdmin.value)
            putString(PREF_USER_ID, _currentUserId.value)
            putString(PREF_DISPLAY_NAME, _displayName.value)
            apply()
        }
    }

    override val currentUser: Flow<String?> = _displayName

    override val isBitflowAdmin: Flow<Boolean> = _isAdmin

    override val currentUserId: Flow<String> = _currentUserId

    override suspend fun checkUsernameAvailable(username: String): Boolean {
        val user = userAccountDao.getUserByUsername(username.trim().lowercase())
        return user == null
    }

    override suspend fun signup(
        username: String,
        displayName: String,
        password: String,
        securityQuestion: String,
        securityAnswer: String
    ): Result<UserAccountEntity> {
        val cleanUsername = username.trim().lowercase()
        val cleanDisplayName = displayName.trim()
        val cleanPassword = password.trim()
        val cleanAnswer = securityAnswer.trim().lowercase()

        return try {
            // Check if username already exists
            val existingUser = userAccountDao.getUserByUsername(cleanUsername)
            if (existingUser != null) {
                return Result.failure(Exception("Username already taken. Please choose another."))
            }

            // Generate salt and hash password
            val passwordSalt = generateSalt()
            val passwordHash = hashPasswordWithSalt(cleanPassword, passwordSalt)
            val combinedPasswordHash = "$passwordSalt:$passwordHash" // Store salt with hash

            val answerSalt = generateSalt()
            val answerHash = hashPasswordWithSalt(cleanAnswer, answerSalt)
            val combinedAnswerHash = "$answerSalt:$answerHash"

            val uniqueUserId = UUID.randomUUID().toString()

            val newUser = UserAccountEntity(
                userId = uniqueUserId,
                username = cleanUsername,
                displayName = cleanDisplayName,
                passwordHash = combinedPasswordHash,
                securityQuestion = securityQuestion,
                securityAnswerHash = combinedAnswerHash,
                createdAt = System.currentTimeMillis(),
                lastLoginAt = System.currentTimeMillis(),
                isActive = true
            )

            userAccountDao.insertUser(newUser)
            Log.d("AuthRepo", "User created: $cleanUsername with UUID: ${uniqueUserId.take(8)}...")

            Result.success(newUser)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun login(username: String, password: String): Result<UserAccountEntity?> {
        val cleanUsername = username.trim().lowercase()
        val cleanPassword = password.trim()

        return try {
            // Fetch user by username
            val user = userAccountDao.getUserByUsername(cleanUsername)

            if (user != null) {
                // Verify password using salted hash
                val storedHash = user.passwordHash
                if (verifyPasswordWithSalt(cleanPassword, storedHash)) {
                    Log.d("AuthRepo", "User authenticated: ${user.username}")
                    Result.success(user)
                } else {
                    Result.success(null) // Wrong password
                }
            } else {
                Result.success(null) // User not found
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun verifySecurityQuestion(
        username: String,
        securityAnswer: String
    ): Result<UserAccountEntity> {
        val cleanUsername = username.trim().lowercase()
        val cleanAnswer = securityAnswer.trim().lowercase()

        return try {
            val user = userAccountDao.getUserByUsername(cleanUsername)

            if (user != null && verifyPasswordWithSalt(cleanAnswer, user.securityAnswerHash)) {
                Result.success(user)
            } else {
                Result.failure(Exception("Incorrect security answer"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun loginWithAccount(account: UserAccountEntity): Result<Unit> {
        return try {
            // Update last login time in DB
            userAccountDao.updateLastLogin(account.userId, System.currentTimeMillis())

            // Update in-memory state
            _isLoggedIn.value = true
            _isAdmin.value = false // No admin backdoor
            _displayName.value = account.displayName
            _currentUserId.value = account.userId

            // Persist to encrypted storage
            saveSessionToStorage()

            Log.d("AuthRepo", "Logged in as: ${account.displayName}")
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun logout() {
        _isLoggedIn.value = false
        _isAdmin.value = false
        _displayName.value = null
        _currentUserId.value = "default_user"
        saveSessionToStorage()
    }

    override suspend fun checkAuth(): Boolean {
        return _isLoggedIn.value
    }

    // --- Secure Hashing Utilities ---

    private fun generateSalt(): String {
        val random = SecureRandom()
        val salt = ByteArray(SALT_LENGTH)
        random.nextBytes(salt)
        return salt.joinToString("") { "%02x".format(it) }
    }

    private fun hashPasswordWithSalt(password: String, salt: String): String {
        val saltedPassword = salt + password
        val bytes = saltedPassword.toByteArray(Charsets.UTF_8)
        val md = MessageDigest.getInstance("SHA-256")
        val digest = md.digest(bytes)
        return digest.joinToString("") { "%02x".format(it) }
    }

    private fun verifyPasswordWithSalt(inputPassword: String, storedCombinedHash: String): Boolean {
        return try {
            val parts = storedCombinedHash.split(":")
            if (parts.size != 2) {
                // Fallback for old un-salted hashes (backward compatibility)
                val inputHash = hashPasswordLegacy(inputPassword)
                inputHash == storedCombinedHash
            } else {
                val salt = parts[0]
                val storedHash = parts[1]
                val inputHash = hashPasswordWithSalt(inputPassword, salt)
                inputHash == storedHash
            }
        } catch (e: Exception) {
            false
        }
    }

    // Legacy hash for backwards compatibility with existing users
    private fun hashPasswordLegacy(password: String): String {
        val bytes = password.toByteArray()
        val md = MessageDigest.getInstance("SHA-256")
        val digest = md.digest(bytes)
        return digest.joinToString("") { "%02x".format(it) }
    }
}
