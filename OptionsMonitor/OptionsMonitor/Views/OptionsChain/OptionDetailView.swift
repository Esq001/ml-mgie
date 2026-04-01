import SwiftUI

struct OptionDetailView: View {
    let contract: OptionContract
    let ticker: String
    let underlyingPrice: Double

    @State private var showCreateAlert = false

    private let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMM d, yyyy"
        return f
    }()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Header
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(contract.contractType == .call ? "CALL" : "PUT")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(contract.contractType == .call ? Color.green : Color.red)
                            .cornerRadius(4)

                        Text("$\(contract.strike, specifier: "%.2f") Strike")
                            .font(.title2)
                            .fontWeight(.bold)

                        Spacer()

                        if contract.inTheMoney {
                            Text("ITM")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(.green)
                        } else {
                            Text("OTM")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Text("Exp: \(dateFormatter.string(from: contract.expiration))")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Divider()

                // Price info
                VStack(alignment: .leading, spacing: 12) {
                    Text("Pricing")
                        .font(.headline)

                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 12) {
                        InfoCell(label: "Last", value: String(format: "$%.2f", contract.lastPrice))
                        InfoCell(label: "Bid", value: String(format: "$%.2f", contract.bid))
                        InfoCell(label: "Ask", value: String(format: "$%.2f", contract.ask))
                        InfoCell(label: "Spread", value: String(format: "$%.2f", contract.spread))
                        InfoCell(label: "Mid", value: String(format: "$%.2f", contract.midPrice))
                        InfoCell(label: "Change", value: String(format: "%+.2f", contract.change),
                                 color: contract.change >= 0 ? .green : .red)
                    }
                }

                Divider()

                // Volume info
                VStack(alignment: .leading, spacing: 12) {
                    Text("Activity")
                        .font(.headline)

                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 12) {
                        InfoCell(label: "Volume", value: formatCompact(contract.volume))
                        InfoCell(label: "Open Int.", value: formatCompact(contract.openInterest))
                        InfoCell(label: "Vol/OI", value: String(format: "%.2f", contract.volumeToOIRatio))
                        InfoCell(label: "IV", value: String(format: "%.1f%%", contract.impliedVolatility * 100))
                    }
                }

                Divider()

                // Greeks
                GreeksDisplayView(contract: contract)

                Divider()

                // Underlying info
                VStack(alignment: .leading, spacing: 8) {
                    Text("Underlying")
                        .font(.headline)
                    HStack {
                        Text(ticker)
                            .fontWeight(.medium)
                        Spacer()
                        Text(String(format: "$%.2f", underlyingPrice))
                            .monospacedDigit()
                    }
                }

                // Create alert button
                Button {
                    showCreateAlert = true
                } label: {
                    Label("Create Alert", systemImage: "bell.badge")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .padding(.top, 8)
            }
            .padding()
        }
        .navigationTitle(contract.contractSymbol)
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showCreateAlert) {
            CreateAlertView(
                contract: contract,
                ticker: ticker,
                alertsViewModel: AlertsViewModel()
            )
        }
    }

    private func formatCompact(_ n: Int) -> String {
        if n >= 1_000_000 { return String(format: "%.1fM", Double(n) / 1_000_000) }
        if n >= 1_000 { return String(format: "%.1fK", Double(n) / 1_000) }
        return "\(n)"
    }
}

struct InfoCell: View {
    let label: String
    let value: String
    var color: Color = .primary

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(color)
                .monospacedDigit()
        }
    }
}
