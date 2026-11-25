package com.example.signalbot

import org.json.JSONObject

class SignalParser {

    private val directionAliases = mapOf(
        "buy" to "buy", "call" to "buy", "up" to "buy", "bull" to "buy",
        "sell" to "sell", "put" to "sell", "down" to "sell", "bear" to "sell"
    )

    private val unitAliases = mapOf(
        "m" to "m", "min" to "m", "mins" to "m", "minute" to "m", "minutes" to "m",
        "s" to "s", "sec" to "s", "secs" to "s", "second" to "s", "seconds" to "s"
    )

    private val textRegex = Regex(
        """(?i)(?P<action>buy|call|up|bull|sell|put|down|bear)\s+
           (?P<symbol>[A-Za-z]{3,6})\s*
           (?:
               (?P<duration>\d+)\s*
               (?P<unit>m|min|mins|minute|minutes|s|sec|secs|second|seconds)?
           )?""".trimIndent()
    )

    data class ParseResult(val signal: Signal, val error: String?)

    fun parse(text: String): ParseResult {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) {
            return ParseResult(Signal("", "", 0), "empty signal")
        }

        return if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
            parseJson(trimmed)
        } else {
            parseText(trimmed)
        }
    }

    private fun parseText(text: String): ParseResult {
        val match = textRegex.find(text) ?: return ParseResult(Signal("", "", 0), "could not parse: $text")
        val actionRaw = match.groups["action"]!!.value.lowercase()
        val action = directionAliases[actionRaw] ?: return ParseResult(Signal("", "", 0), "unknown action: $actionRaw")
        val symbol = match.groups["symbol"]!!.value.uppercase()
        val durationStr = match.groups["duration"]!!.value
        val duration = if (durationStr.isNotBlank()) durationStr.toIntOrNull() ?: 5 else 5
        val unitRaw = match.groups["unit"]!!.value
        val unit = if (unitRaw.isNotBlank()) unitAliases[unitRaw.lowercase()] ?: "m" else "m"
        return ParseResult(
            Signal(action = action, symbol = symbol, duration = duration, durationUnit = unit, raw = text),
            null
        )
    }

    private fun parseJson(text: String): ParseResult {
        return try {
            val obj = JSONObject(text)
            val actionRaw = obj.optString("action", "").lowercase()
            val action = directionAliases[actionRaw] ?: return ParseResult(Signal("", "", 0), "missing/unknown action")
            val symbol = obj.optString("symbol", "").uppercase()
            if (symbol.isEmpty()) return ParseResult(Signal("", "", 0), "missing symbol")
            val duration = obj.optInt("duration", 5).coerceAtLeast(1)
            val unit = unitAliases[obj.optString("duration_unit", obj.optString("unit", "m")).lowercase()] ?: "m"
            val confidence = obj.optDouble("confidence", 1.0).coerceIn(0.0, 1.0)
            ParseResult(
                Signal(action, symbol, duration, unit, confidence, source = "json", raw = text),
                null
            )
        } catch (e: Exception) {
            ParseResult(Signal("", "", 0), "invalid JSON: ${e.message}")
        }
    }

    fun validate(signal: Signal): List<String> {
        val errors = mutableListOf<String>()
        if (!listOf("buy", "sell").contains(signal.action.lowercase())) errors.add("invalid action: ${signal.action}")
        if (!Regex("^[A-Za-z]{3,6}$").matches(signal.symbol)) errors.add("invalid symbol: ${signal.symbol}")
        if (signal.duration < 1) errors.add("duration must be >= 1")
        if (signal.confidence !in 0.0..1.0) errors.add("confidence out of range")
        return errors
    }
}
