package com.bitflow.finance.data.local.dao

import androidx.room.*
import com.bitflow.finance.data.local.entity.HoldingEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface HoldingDao {
    @Query("SELECT * FROM holdings WHERE userId = :userId ORDER BY name ASC")
    fun getHoldings(userId: String): Flow<List<HoldingEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertHolding(holding: HoldingEntity)

    @Delete
    suspend fun deleteHolding(holding: HoldingEntity)
    
    @Update
    suspend fun updateHolding(holding: HoldingEntity)
    
    @Query("SELECT SUM(quantity * currentMarketPrice) FROM holdings WHERE userId = :userId")
    fun getTotalPortfolioValue(userId: String): Flow<Double?>
}
