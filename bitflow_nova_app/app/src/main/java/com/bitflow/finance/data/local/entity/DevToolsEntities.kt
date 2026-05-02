package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

// ==================== CODE SNIPPETS ====================
@Entity(tableName = "code_snippets")
data class CodeSnippetEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val title: String,
    val description: String = "",
    val code: String,
    val language: String, // kotlin, python, java, sql, etc.
    val tags: String = "", // Comma-separated
    val category: String = "General", // Android, Backend, Database, etc.
    val isFavorite: Boolean = false,
    val usageCount: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)

// ==================== API REQUESTS ====================
@Entity(tableName = "api_collections")
data class ApiCollectionEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val name: String,
    val description: String = "",
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "api_requests")
data class ApiRequestEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val collectionId: Long? = null,
    val name: String,
    val method: String = "GET", // GET, POST, PUT, DELETE, PATCH
    val url: String,
    val headers: String = "{}", // JSON object
    val body: String = "",
    val bodyType: String = "none", // none, json, form, raw
    val authType: String = "none", // none, bearer, basic, apikey
    val authValue: String = "",
    val createdAt: Long = System.currentTimeMillis(),
    val lastUsedAt: Long? = null
)

@Entity(tableName = "api_environments")
data class ApiEnvironmentEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val name: String, // dev, staging, prod
    val variables: String = "{}", // JSON object of key-value pairs
    val isActive: Boolean = false,
    val createdAt: Long = System.currentTimeMillis()
)

// ==================== SAVED COLORS ====================
@Entity(tableName = "saved_colors")
data class SavedColorEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val hex: String, // #RRGGBB
    val name: String = "",
    val category: String = "default", // palette name
    val createdAt: Long = System.currentTimeMillis()
)

// ==================== REGEX PATTERNS ====================
@Entity(tableName = "saved_regex")
data class SavedRegexEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val name: String,
    val pattern: String,
    val testInput: String = "",
    val description: String = "",
    val category: String = "custom",
    val createdAt: Long = System.currentTimeMillis()
)

// ==================== ENV PROFILES ====================
@Entity(tableName = "env_profiles")
data class EnvProfileEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val name: String, // Project name or profile name
    val variables: String = "{}", // JSON key-value pairs
    val filePath: String = "", // Associated .env file path if any
    val isActive: Boolean = false,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)
