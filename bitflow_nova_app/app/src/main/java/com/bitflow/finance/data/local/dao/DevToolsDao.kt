package com.bitflow.finance.data.local.dao

import androidx.room.*
import com.bitflow.finance.data.local.entity.*
import kotlinx.coroutines.flow.Flow

// ==================== CODE SNIPPETS DAO ====================
@Dao
interface CodeSnippetDao {
    @Query("SELECT * FROM code_snippets WHERE userId = :userId ORDER BY isFavorite DESC, usageCount DESC, updatedAt DESC")
    fun getAllSnippets(userId: String): Flow<List<CodeSnippetEntity>>
    
    @Query("SELECT * FROM code_snippets WHERE userId = :userId AND language = :language ORDER BY usageCount DESC")
    fun getSnippetsByLanguage(userId: String, language: String): Flow<List<CodeSnippetEntity>>
    
    @Query("SELECT * FROM code_snippets WHERE userId = :userId AND category = :category ORDER BY usageCount DESC")
    fun getSnippetsByCategory(userId: String, category: String): Flow<List<CodeSnippetEntity>>
    
    @Query("SELECT * FROM code_snippets WHERE userId = :userId AND (title LIKE '%' || :query || '%' OR code LIKE '%' || :query || '%' OR tags LIKE '%' || :query || '%') ORDER BY usageCount DESC")
    fun searchSnippets(userId: String, query: String): Flow<List<CodeSnippetEntity>>
    
    @Query("SELECT DISTINCT language FROM code_snippets WHERE userId = :userId ORDER BY language")
    fun getAllLanguages(userId: String): Flow<List<String>>
    
    @Query("SELECT DISTINCT category FROM code_snippets WHERE userId = :userId ORDER BY category")
    fun getAllCategories(userId: String): Flow<List<String>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(snippet: CodeSnippetEntity): Long
    
    @Update
    suspend fun update(snippet: CodeSnippetEntity)
    
    @Delete
    suspend fun delete(snippet: CodeSnippetEntity)
    
    @Query("UPDATE code_snippets SET usageCount = usageCount + 1 WHERE id = :id")
    suspend fun incrementUsage(id: Long)
    
    @Query("UPDATE code_snippets SET isFavorite = :isFavorite WHERE id = :id")
    suspend fun toggleFavorite(id: Long, isFavorite: Boolean)
}

// ==================== API TESTER DAOs ====================
@Dao
interface ApiCollectionDao {
    @Query("SELECT * FROM api_collections WHERE userId = :userId ORDER BY name")
    fun getAllCollections(userId: String): Flow<List<ApiCollectionEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(collection: ApiCollectionEntity): Long
    
    @Update
    suspend fun update(collection: ApiCollectionEntity)
    
    @Delete
    suspend fun delete(collection: ApiCollectionEntity)
}

@Dao
interface ApiRequestDao {
    @Query("SELECT * FROM api_requests WHERE userId = :userId ORDER BY lastUsedAt DESC, name")
    fun getAllRequests(userId: String): Flow<List<ApiRequestEntity>>
    
    @Query("SELECT * FROM api_requests WHERE userId = :userId AND collectionId = :collectionId ORDER BY name")
    fun getRequestsByCollection(userId: String, collectionId: Long): Flow<List<ApiRequestEntity>>
    
    @Query("SELECT * FROM api_requests WHERE userId = :userId AND collectionId IS NULL ORDER BY name")
    fun getUncategorizedRequests(userId: String): Flow<List<ApiRequestEntity>>
    
    @Query("SELECT * FROM api_requests WHERE userId = :userId AND (name LIKE '%' || :query || '%' OR url LIKE '%' || :query || '%')")
    fun searchRequests(userId: String, query: String): Flow<List<ApiRequestEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(request: ApiRequestEntity): Long
    
    @Update
    suspend fun update(request: ApiRequestEntity)
    
    @Delete
    suspend fun delete(request: ApiRequestEntity)
    
    @Query("UPDATE api_requests SET lastUsedAt = :time WHERE id = :id")
    suspend fun updateLastUsed(id: Long, time: Long)
}

@Dao
interface ApiEnvironmentDao {
    @Query("SELECT * FROM api_environments WHERE userId = :userId ORDER BY name")
    fun getAllEnvironments(userId: String): Flow<List<ApiEnvironmentEntity>>
    
    @Query("SELECT * FROM api_environments WHERE userId = :userId AND isActive = 1 LIMIT 1")
    fun getActiveEnvironment(userId: String): Flow<ApiEnvironmentEntity?>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(env: ApiEnvironmentEntity): Long
    
    @Update
    suspend fun update(env: ApiEnvironmentEntity)
    
    @Delete
    suspend fun delete(env: ApiEnvironmentEntity)
    
    @Query("UPDATE api_environments SET isActive = 0 WHERE userId = :userId")
    suspend fun deactivateAll(userId: String)
    
    @Query("UPDATE api_environments SET isActive = 1 WHERE id = :id")
    suspend fun activate(id: Long)
}

// ==================== SAVED COLORS DAO ====================
@Dao
interface SavedColorDao {
    @Query("SELECT * FROM saved_colors WHERE userId = :userId ORDER BY category, createdAt DESC")
    fun getAllColors(userId: String): Flow<List<SavedColorEntity>>
    
    @Query("SELECT * FROM saved_colors WHERE userId = :userId AND category = :category ORDER BY createdAt DESC")
    fun getColorsByCategory(userId: String, category: String): Flow<List<SavedColorEntity>>
    
    @Query("SELECT DISTINCT category FROM saved_colors WHERE userId = :userId ORDER BY category")
    fun getAllCategories(userId: String): Flow<List<String>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(color: SavedColorEntity): Long
    
    @Delete
    suspend fun delete(color: SavedColorEntity)
    
    @Query("DELETE FROM saved_colors WHERE userId = :userId AND category = :category")
    suspend fun deleteCategory(userId: String, category: String)
}

// ==================== SAVED REGEX DAO ====================
@Dao
interface SavedRegexDao {
    @Query("SELECT * FROM saved_regex WHERE userId = :userId ORDER BY category, name")
    fun getAllPatterns(userId: String): Flow<List<SavedRegexEntity>>
    
    @Query("SELECT * FROM saved_regex WHERE userId = :userId AND category = :category ORDER BY name")
    fun getPatternsByCategory(userId: String, category: String): Flow<List<SavedRegexEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(regex: SavedRegexEntity): Long
    
    @Update
    suspend fun update(regex: SavedRegexEntity)
    
    @Delete
    suspend fun delete(regex: SavedRegexEntity)
}

// ==================== ENV PROFILES DAO ====================
@Dao
interface EnvProfileDao {
    @Query("SELECT * FROM env_profiles WHERE userId = :userId ORDER BY name")
    fun getAllProfiles(userId: String): Flow<List<EnvProfileEntity>>
    
    @Query("SELECT * FROM env_profiles WHERE userId = :userId AND isActive = 1 LIMIT 1")
    fun getActiveProfile(userId: String): Flow<EnvProfileEntity?>
    
    @Query("SELECT * FROM env_profiles WHERE id = :id")
    suspend fun getProfileById(id: Long): EnvProfileEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(profile: EnvProfileEntity): Long
    
    @Update
    suspend fun update(profile: EnvProfileEntity)
    
    @Delete
    suspend fun delete(profile: EnvProfileEntity)
    
    @Query("UPDATE env_profiles SET isActive = 0 WHERE userId = :userId")
    suspend fun deactivateAll(userId: String)
    
    @Query("UPDATE env_profiles SET isActive = 1 WHERE id = :id")
    suspend fun activate(id: Long)
}
