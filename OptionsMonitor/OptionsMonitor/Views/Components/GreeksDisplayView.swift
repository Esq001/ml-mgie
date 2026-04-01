import SwiftUI

struct GreeksDisplayView: View {
    let contract: OptionContract

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Greeks")
                .font(.headline)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                GreekCard(
                    name: "Delta (Δ)",
                    value: contract.delta,
                    format: "%.4f",
                    description: "Price sensitivity to $1 move in underlying"
                )
                GreekCard(
                    name: "Gamma (Γ)",
                    value: contract.gamma,
                    format: "%.4f",
                    description: "Rate of change of delta"
                )
                GreekCard(
                    name: "Theta (Θ)",
                    value: contract.theta,
                    format: "%.4f",
                    description: "Daily time decay"
                )
                GreekCard(
                    name: "Vega (V)",
                    value: contract.vega,
                    format: "%.4f",
                    description: "Sensitivity to 1% IV change"
                )
            }
        }
    }
}

struct GreekCard: View {
    let name: String
    let value: Double?
    let format: String
    let description: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(name)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value.map { String(format: format, $0) } ?? "N/A")
                .font(.title3)
                .fontWeight(.semibold)
                .monospacedDigit()
            Text(description)
                .font(.caption2)
                .foregroundColor(.secondary)
                .lineLimit(2)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}
