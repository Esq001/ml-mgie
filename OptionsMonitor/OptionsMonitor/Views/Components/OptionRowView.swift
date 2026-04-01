import SwiftUI

struct OptionRowView: View {
    let contract: OptionContract
    let underlyingPrice: Double

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                // Strike price with ITM/OTM indicator
                HStack(spacing: 4) {
                    Circle()
                        .fill(contract.inTheMoney ? Color.green : Color.gray.opacity(0.3))
                        .frame(width: 8, height: 8)
                    Text("$\(contract.strike, specifier: "%.2f")")
                        .font(.headline)
                        .monospacedDigit()
                }

                Spacer()

                // Last price and change
                VStack(alignment: .trailing, spacing: 2) {
                    Text("$\(contract.lastPrice, specifier: "%.2f")")
                        .font(.headline)
                        .monospacedDigit()
                    Text("\(contract.change >= 0 ? "+" : "")\(contract.change, specifier: "%.2f") (\(contract.percentChange, specifier: "%.1f")%)")
                        .font(.caption)
                        .foregroundColor(contract.change >= 0 ? .green : .red)
                }
            }

            HStack(spacing: 16) {
                LabeledValue(label: "Bid", value: String(format: "%.2f", contract.bid))
                LabeledValue(label: "Ask", value: String(format: "%.2f", contract.ask))
                LabeledValue(label: "Vol", value: formatCompact(contract.volume))
                LabeledValue(label: "OI", value: formatCompact(contract.openInterest))
                LabeledValue(label: "IV", value: String(format: "%.1f%%", contract.impliedVolatility * 100))
            }
            .font(.caption)
            .foregroundColor(.secondary)

            // Greeks row
            if contract.delta != nil {
                HStack(spacing: 12) {
                    GreekChip(name: "Δ", value: contract.delta)
                    GreekChip(name: "Γ", value: contract.gamma)
                    GreekChip(name: "Θ", value: contract.theta)
                    GreekChip(name: "V", value: contract.vega)
                }
            }
        }
        .padding(.vertical, 4)
    }

    private func formatCompact(_ n: Int) -> String {
        if n >= 1_000_000 { return String(format: "%.1fM", Double(n) / 1_000_000) }
        if n >= 1_000 { return String(format: "%.1fK", Double(n) / 1_000) }
        return "\(n)"
    }
}

struct LabeledValue: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
            Text(value)
                .monospacedDigit()
        }
    }
}

struct GreekChip: View {
    let name: String
    let value: Double?

    var body: some View {
        if let value = value {
            HStack(spacing: 2) {
                Text(name)
                    .font(.caption2)
                    .foregroundColor(.secondary)
                Text(String(format: "%.3f", value))
                    .font(.caption)
                    .monospacedDigit()
            }
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(Color(.systemGray6))
            .cornerRadius(4)
        }
    }
}
