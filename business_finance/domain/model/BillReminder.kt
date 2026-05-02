package com.bitflow.finance.domain.model

data class BillReminder(
    val id: Long = 0,
    val name: String,
    val amount: Double,
    val dueDay: Int,
    val reminderDaysBefore: Int = 3,
    val isRecurring: Boolean = true,
    val categoryId: Long? = null,
    val isActive: Boolean = true,
    val createdAt: Long = System.currentTimeMillis()
) {
    val dueDayFormatted: String
        get() = when (dueDay) {
            1, 21, 31 -> "${dueDay}st"
            2, 22 -> "${dueDay}nd"
            3, 23 -> "${dueDay}rd"
            else -> "${dueDay}th"
        }
}
