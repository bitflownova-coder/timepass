package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Tracks discussions with clients about potential payments
 * Each discussion has an expected amount that can be updated
 * Once finalized, it converts to an IncomePayment
 */
@Entity(
    tableName = "client_discussions",
    foreignKeys = [
        ForeignKey(
            entity = ClientEntity::class,
            parentColumns = ["id"],
            childColumns = ["clientId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("clientId")]
)
data class ClientDiscussionEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val clientId: Long,
    val title: String,                    // Brief description of work/project
    val description: String = "",         // Detailed notes
    val expectedAmount: Double,           // Discussed amount
    val discussionDate: Long = System.currentTimeMillis(),
    val lastUpdated: Long = System.currentTimeMillis(),
    val status: String = "pending",       // pending, negotiating, finalized, cancelled
    val notes: String = "",               // Update notes from each discussion
    val createdAt: Long = System.currentTimeMillis()
)
