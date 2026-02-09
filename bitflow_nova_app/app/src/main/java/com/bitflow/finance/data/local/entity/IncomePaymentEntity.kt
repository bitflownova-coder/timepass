package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Records actual income/payments received
 * Can be linked to a discussion or standalone
 * Links to invoices for auto-generation
 */
@Entity(
    tableName = "income_payments",
    foreignKeys = [
        ForeignKey(
            entity = ClientEntity::class,
            parentColumns = ["id"],
            childColumns = ["clientId"],
            onDelete = ForeignKey.SET_NULL
        ),
        ForeignKey(
            entity = ClientDiscussionEntity::class,
            parentColumns = ["id"],
            childColumns = ["discussionId"],
            onDelete = ForeignKey.SET_NULL
        )
    ],
    indices = [Index("clientId"), Index("discussionId"), Index("invoiceId")]
)
data class IncomePaymentEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    val clientId: Long? = null,           // Optional: if from a client
    val discussionId: Long? = null,       // Optional: if originated from discussion
    val invoiceId: Long? = null,          // Link to generated invoice
    
    val amount: Double,
    val description: String,              // What the payment was for
    val paymentDate: Long = System.currentTimeMillis(),
    val paymentMode: String = "bank",     // bank, cash, upi, cheque, other
    val reference: String = "",           // Transaction ref/UTR number
    
    val invoiceGenerated: Boolean = false,
    val invoiceNumber: String? = null,
    
    val notes: String = "",
    val createdAt: Long = System.currentTimeMillis()
)
