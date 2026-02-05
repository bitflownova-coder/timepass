package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

enum class AssetType {
    STOCK,
    MUTUAL_FUND,
    FD,
    GOLD,
    CRYPTO,
    REAL_ESTATE,
    OTHER
}

@Entity(tableName = "holdings")
data class HoldingEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val userId: String,
    val name: String,              // "HDFC Bank", "Nifty 50 Index"
    val type: AssetType,
    val quantity: Double,          // 10.0
    val averageBuyPrice: Double,   // 1500.0
    val currentMarketPrice: Double,// 1600.0 (User updates manually)
    val investedDate: Long = System.currentTimeMillis(),
    val notes: String = ""
) {
    val totalInvested: Double
        get() = quantity * averageBuyPrice
        
    val currentValue: Double
        get() = quantity * currentMarketPrice
        
    val profitLoss: Double
        get() = currentValue - totalInvested
        
    val returnsPercentage: Double
        get() = if (totalInvested > 0) (profitLoss / totalInvested) * 100 else 0.0
}
