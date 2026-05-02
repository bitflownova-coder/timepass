package com.bitflow.finance.domain.model

enum class CategoryType {
    EXPENSE, INCOME, TRANSFER
}

data class Category(
    val id: Long = 0,
    val name: String,
    val type: CategoryType,
    val icon: String, // Emoji or icon name
    val color: Int,
    // Human-centric enhancements
    val usageCount: Int = 0,
    val lastUsedAt: Long? = null,
    val isUserDeletable: Boolean = true,
    val isHidden: Boolean = false,
    val sortOrder: Int = 0 // Higher = shown first
)

object DefaultCategories {
    val indianContext = listOf(
        Category(name = "Kirana & Groceries", type = CategoryType.EXPENSE, icon = "🥦", color = 0xFF4CAF50.toInt()),
        Category(name = "Zomato/Swiggy", type = CategoryType.EXPENSE, icon = "🍔", color = 0xFFF44336.toInt()),
        Category(name = "UPI Transfers", type = CategoryType.TRANSFER, icon = "💸", color = 0xFF2196F3.toInt()),
        Category(name = "Rent", type = CategoryType.EXPENSE, icon = "🏠", color = 0xFF9C27B0.toInt()),
        Category(name = "Fuel/Transport", type = CategoryType.EXPENSE, icon = "⛽", color = 0xFFFF9800.toInt()),
        Category(name = "Salary", type = CategoryType.INCOME, icon = "💰", color = 0xFF00BCD4.toInt()),
        Category(name = "Investment", type = CategoryType.TRANSFER, icon = "📈", color = 0xFF3F51B5.toInt()),
        Category(name = "Utilities", type = CategoryType.EXPENSE, icon = "💡", color = 0xFFFFC107.toInt()),
        Category(name = "Entertainment", type = CategoryType.EXPENSE, icon = "🎬", color = 0xFFE91E63.toInt()),
        Category(name = "Medical", type = CategoryType.EXPENSE, icon = "💊", color = 0xFFF44336.toInt())
    )
}
