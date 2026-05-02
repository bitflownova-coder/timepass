package com.bitflow.finance.domain.model

enum class FinancialPersona(val title: String, val description: String, val emoji: String) {
    CONSCIOUS_SAVER("Conscious Saver", "You prioritize saving and have high control over discretionary spending.", "🛡️"),
    IMPULSE_SPENDER("Impulse Spender", "You tend to make frequent discretionary purchases, often in bursts.", "⚡"),
    LIFESTYLE_INFLATOR("Lifestyle Inflator", "Your spending increases significantly as your income rises.", "📈"),
    PAYCHECK_TO_PAYCHECK("Paycheck Survivor", "Your balance frequently drops near zero before payday.", "🏃"),
    DEBT_PYRAMID("Debt Balancer", "A significant portion of your income goes towards debt servicing.", "⚖️"),
    BALANCED_BUILDER("Balanced Builder", "You maintain a healthy balance between needs, wants, and savings.", "🏗️"),
    UNCATEGORIZED("Newcomer", "Not enough data to analyze your style yet.", "🐣")
}
