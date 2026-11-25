package com.example.signalbot

data class DailyStats(
    var date: String = "",
    var trades: Int = 0,
    var wins: Int = 0,
    var losses: Int = 0,
    var totalProfit: Double = 0.0,
    var totalVolume: Double = 0.0
) {
    val winRate: Double get() = if (trades == 0) 0.0 else wins.toDouble() / trades
}

class RiskManager(
    val maxDailyLoss: Double = 20.0,
    val maxDailyProfit: Double = 100.0,
    val maxConcurrentTrades: Int = 1,
    val minConfidence: Double = 0.0
) {
    private val stats = DailyStats()
    private val openTrades = mutableSetOf<String>()

    private fun today(): String =
        java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault())
            .format(java.util.Date())

    fun canTrade(signal: Signal, amount: Double): Pair<Boolean, String> {
        stats.date = today()
        if (amount <= 0) return Pair(false, "amount must be positive")
        if (openTrades.size >= maxConcurrentTrades) return Pair(false, "max concurrent trades reached")
        if (stats.totalProfit <= -maxDailyLoss) return Pair(false, "daily loss limit reached")
        if (stats.totalProfit >= maxDailyProfit) return Pair(false, "daily profit target reached")
        if (signal.confidence < minConfidence) return Pair(false, "confidence below minimum")
        return Pair(true, "")
    }

    fun openTrade(id: String) { openTrades.add(id) }
    fun closeTrade(id: String) { openTrades.remove(id) }

    fun record(result: Signal) {
        stats.trades++
        stats.totalVolume += if (result.status == "win") 1.0 else 0.0 // placeholder volume
        stats.totalProfit += result.profit
        if (result.profit > 0) stats.wins++ else if (result.profit < 0) stats.losses++
        openTrades.clear()
    }

    fun summary(): String = "Trades: ${stats.trades} | Wins: ${stats.wins} | Losses: ${stats.losses} | " +
        "Profit: ${"%.2f".format(stats.totalProfit)} | WinRate: ${"%.0f".format(stats.winRate * 100)}%"
}
