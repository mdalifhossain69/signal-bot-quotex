package com.example.signalbot

import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class SignalAdapter(private val items: MutableList<Signal>) : RecyclerView.Adapter<SignalAdapter.ViewHolder>() {

    class ViewHolder(val view: android.view.View) : RecyclerView.ViewHolder(view) {
        val action: TextView = view.findViewById(R.id.signalAction)
        val symbol: TextView = view.findViewById(R.id.signalSymbol)
        val detail: TextView = view.findViewById(R.id.signalDetail)
        val status: TextView = view.findViewById(R.id.signalStatus)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_signal, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val signal = items[position]
        holder.action.text = signal.action.capitalize()
        holder.symbol.text = signal.symbol
        holder.detail.text = "${signal.displayText()}  conf=${signal.confidence}"
        holder.status.text = when (signal.status) {
            "win" -> "+${"%.2f".format(signal.profit)}"
            "loss" -> "-${"%.2f".format(signal.profit.absoluteValue)}"
            else -> signal.status
        }
        holder.status.setTextColor(
            when (signal.status) {
                "win" -> android.graphics.Color.GREEN
                "loss" -> android.graphics.Color.RED
                else -> android.graphics.Color.GRAY
            }
        )
    }

    override fun getItemCount() = items.size

    fun add(signal: Signal) { items.add(0, signal); notifyItemInserted(0) }
    fun clear() { items.clear(); notifyDataSetChanged() }
}
