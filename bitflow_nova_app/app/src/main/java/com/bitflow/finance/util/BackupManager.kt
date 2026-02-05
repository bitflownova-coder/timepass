package com.bitflow.finance.util

import android.content.Context
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

/**
 * Provides encrypted backup and restore functionality for the app database.
 * Uses AES-256-GCM encryption with PBKDF2 key derivation.
 */
object BackupManager {
    
    private const val ALGORITHM = "AES/GCM/NoPadding"
    private const val KEY_ALGORITHM = "AES"
    private const val KEY_DERIVATION = "PBKDF2WithHmacSHA256"
    private const val KEY_LENGTH = 256
    private const val ITERATION_COUNT = 65536
    private const val GCM_TAG_LENGTH = 128
    private const val SALT_LENGTH = 16
    private const val IV_LENGTH = 12
    
    data class BackupResult(
        val success: Boolean,
        val filePath: String? = null,
        val error: String? = null
    )
    
    /**
     * Creates an encrypted backup of the database.
     * The backup file contains: [salt (16 bytes)][iv (12 bytes)][encrypted data]
     */
    fun createEncryptedBackup(
        context: Context,
        password: String,
        databaseName: String = "finance_database"
    ): BackupResult {
        return try {
            val dbFile = context.getDatabasePath(databaseName)
            if (!dbFile.exists()) {
                return BackupResult(false, error = "Database not found")
            }
            
            // Read database bytes
            val dbBytes = FileInputStream(dbFile).use { it.readBytes() }
            
            // Generate salt and IV
            val random = SecureRandom()
            val salt = ByteArray(SALT_LENGTH).also { random.nextBytes(it) }
            val iv = ByteArray(IV_LENGTH).also { random.nextBytes(it) }
            
            // Derive key from password
            val key = deriveKey(password, salt)
            
            // Encrypt
            val cipher = Cipher.getInstance(ALGORITHM)
            cipher.init(Cipher.ENCRYPT_MODE, key, GCMParameterSpec(GCM_TAG_LENGTH, iv))
            val encryptedBytes = cipher.doFinal(dbBytes)
            
            // Create backup file
            val backupDir = File(context.getExternalFilesDir(null), "backups")
            backupDir.mkdirs()
            val backupFile = File(backupDir, "finance_backup_${System.currentTimeMillis()}.bak")
            
            // Write: salt + iv + encrypted data
            FileOutputStream(backupFile).use { fos ->
                fos.write(salt)
                fos.write(iv)
                fos.write(encryptedBytes)
            }
            
            BackupResult(true, filePath = backupFile.absolutePath)
        } catch (e: Exception) {
            BackupResult(false, error = e.message ?: "Encryption failed")
        }
    }
    
    /**
     * Restores the database from an encrypted backup file.
     */
    fun restoreFromBackup(
        context: Context,
        backupFile: File,
        password: String,
        databaseName: String = "finance_database"
    ): BackupResult {
        return try {
            if (!backupFile.exists()) {
                return BackupResult(false, error = "Backup file not found")
            }
            
            val backupBytes = FileInputStream(backupFile).use { it.readBytes() }
            
            if (backupBytes.size < SALT_LENGTH + IV_LENGTH + 16) {
                return BackupResult(false, error = "Invalid backup file")
            }
            
            // Extract salt, iv, and encrypted data
            val salt = backupBytes.copyOfRange(0, SALT_LENGTH)
            val iv = backupBytes.copyOfRange(SALT_LENGTH, SALT_LENGTH + IV_LENGTH)
            val encryptedData = backupBytes.copyOfRange(SALT_LENGTH + IV_LENGTH, backupBytes.size)
            
            // Derive key from password
            val key = deriveKey(password, salt)
            
            // Decrypt
            val cipher = Cipher.getInstance(ALGORITHM)
            cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(GCM_TAG_LENGTH, iv))
            val decryptedBytes = cipher.doFinal(encryptedData)
            
            // Write to database file
            val dbFile = context.getDatabasePath(databaseName)
            FileOutputStream(dbFile).use { it.write(decryptedBytes) }
            
            BackupResult(true, filePath = dbFile.absolutePath)
        } catch (e: Exception) {
            BackupResult(false, error = "Decryption failed. Wrong password?")
        }
    }
    
    private fun deriveKey(password: String, salt: ByteArray): SecretKeySpec {
        val factory = SecretKeyFactory.getInstance(KEY_DERIVATION)
        val spec = PBEKeySpec(password.toCharArray(), salt, ITERATION_COUNT, KEY_LENGTH)
        val secretKey = factory.generateSecret(spec)
        return SecretKeySpec(secretKey.encoded, KEY_ALGORITHM)
    }
}
