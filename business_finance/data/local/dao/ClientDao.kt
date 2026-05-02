package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.ClientEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ClientDao {
    
    @Query("SELECT * FROM clients WHERE userId = :userId ORDER BY name ASC")
    fun getAllClients(userId: String): Flow<List<ClientEntity>>
    
    @Query("SELECT * FROM clients WHERE id = :id AND userId = :userId")
    suspend fun getClientById(id: Long, userId: String): ClientEntity?
    
    @Query("SELECT * FROM clients WHERE name LIKE '%' || :query || '%' AND userId = :userId")
    fun searchClients(query: String, userId: String): Flow<List<ClientEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertClient(client: ClientEntity): Long
    
    @Update
    suspend fun updateClient(client: ClientEntity)
    
    @Delete
    suspend fun deleteClient(client: ClientEntity)
}
