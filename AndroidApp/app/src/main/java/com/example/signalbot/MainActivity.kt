package com.example.signalbot

import android.app.AlertDialog
import android.os.Bundle
import android.text.InputType
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.signalbot.databinding.ActivityMainBinding
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var parser: SignalParser
    private lateinit var simulator: TradeSimulator
    private lateinit var risk: RiskManager
    private lateinit var adapter: SignalAdapter

    private val executor = Executors.newSingleThreadExecutor()
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        parser = SignalParser()
        simulator = TradeSimulator()
        risk = RiskManager()
        adapter = SignalAdapter(mutableListOf())

        binding.recycler.layoutManager = LinearLayoutManager(this)
        binding.recycler.adapter = adapter

        binding.fabAdd.setOnClickListener { showInputDialog() }
        binding.btnStatus.setOnClickListener { showStatus() }
        binding.btnClear.setOnClickListener { adapter.clear(); binding.txtStatus.text = "" }

        binding.txtStatus.text = "Signal Bot ready. Tap + to add a signal."
    }

    private fun showInputDialog() {
        val input = EditText(this)
        input.inputType = InputType.TYPE_CLASS_TEXT
        input.hint = "e.g. BUY EURUSD 5m or {\"action\":\"BUY\",\"symbol\":\"EURUSD\"}"

        AlertDialog.Builder(this)
            .setTitle("Enter Signal")
            .setView(input)
            .setPositiveButton("Place") { _, _ ->
                val text = input.text.toString()
                handleSignal(text)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun handleSignal(text: String) {
        val result = parser.parse(text)
        if (result.error != null) {
            toast("Parse error: ${result.error}")
            return
        }
        val signal = result.signal
        val errors = parser.validate(signal)
        if (errors.isNotEmpty()) {
            toast("Invalid signal: ${errors.joinToString(", ")}")
            return
        }

        val amount = 1.0
        val allowed = risk.canTrade(signal, amount)
        if (!allowed.first) {
            toast("Rejected: ${allowed.second}")
            return
        }

        executor.execute {
            val executed = simulator.execute(signal, amount)
            risk.record(executed)
            mainHandler.post {
                adapter.add(executed)
                binding.txtStatus.text = risk.summary()
                toast("${executed.action} ${executed.symbol} -> ${executed.status}")
            }
        }
    }

    private fun showStatus() {
        AlertDialog.Builder(this)
            .setTitle("Status")
            .setMessage(risk.summary())
            .setPositiveButton("OK", null)
            .show()
    }

    private fun toast(msg: String) {
        mainHandler.post { Toast.makeText(this, msg, Toast.LENGTH_SHORT).show() }
    }

    override fun onDestroy() {
        executor.shutdown()
        super.onDestroy()
    }
}
