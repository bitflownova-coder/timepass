package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Records business expenses/output
 * Categories: one-time or subscription
 * Requires bill attachment for proper records
 */
@Entity(tableName = "expense_records")
data class ExpenseRecordEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: String,
    
    val amount: Double,
    val description: String,              // What was purchased/spent on
    val reason: String,                   // Why it was needed
    
    val expenseType: String,              // "one_time" or "subscription"
    val category: String,                 // software, hosting, tools, office, marketing, etc.
    
    val expenseDate: Long = System.currentTimeMillis(),
    val paymentMode: String = "bank",     // bank, cash, upi, card, other
    val vendor: String = "",              // Who was paid
    
    // For subscriptions
    val isRecurring: Boolean = false,
    val recurringPeriod: String? = null,  // monthly, yearly, quarterly
    val nextDueDate: Long? = null,
    
    // Bill attachment (stored as file path or base64)
    val billAttached: Boolean = false,
    val billPath: String? = null,         // Local file path to bill image/PDF
    val billNote: String = "",            // Additional bill notes
    
    val notes: String = "",
    val createdAt: Long = System.currentTimeMillis()
) {
    companion object {
        val EXPENSE_CATEGORIES = listOf(
            "Software & Tools",
            "Hosting & Servers", 
            "Domain & SSL",
            "Marketing & Ads",
            "Office Supplies",
            "Equipment",
            "Travel",
            "Communication",
            "Professional Services",
            "Subscriptions",
            "Utilities",
            "Other"
        )
        
        val EXPENSE_TYPES = listOf("one_time", "subscription")
        val RECURRING_PERIODS = listOf("monthly", "quarterly", "yearly")
    }
}
