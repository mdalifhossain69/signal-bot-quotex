package com.example.signalbot

import kotlin.random.Random

class TradeSimulator(private val winRate: Double = 0.55, private val payout: Double = 0.80) {

    fun execute(signal: Signal, amount: Double): Signal {
        val win = Random.nextDouble() < winRate
        val profit = if (win) round2(amount * payout) else -round2(amount)
        return signal.copy(
            status = if (win) "win" else "loss",
            profit = profit
        )
    }

    private fun round2(value: Double): Double = (value * 100).roundToInt() / 100.0
}
