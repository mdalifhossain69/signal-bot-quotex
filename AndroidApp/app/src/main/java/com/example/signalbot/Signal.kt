package com.example.signalbot

data class Signal(
    val action: String,        // "buy" or "sell"
    val symbol: String,
    val duration: Int,
    val durationUnit: String = "m", // "m" or "s"
    val confidence: Double = 1.0,
    val source: String = "manual",
    val raw: String = "",
    val timestamp: Long = System.currentTimeMillis(),
    var profit: Double = 0.0,
    var status: String = "pending" // pending, win, loss
) {
    fun isBuy(): Boolean = action.equals("buy", ignoreCase = true)
    fun payoutPercent(): Double = 80.0 // typical Quotex payout
    fun displayText(): String = "${action.capitalize()} $symbol ${duration}$durationUnit"
}
