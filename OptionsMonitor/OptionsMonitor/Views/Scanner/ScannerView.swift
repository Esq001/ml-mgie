import SwiftUI

struct ScannerView: View {
    @StateObject private var viewModel = ScannerViewModel()

    private let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "h:mm:ss a"
        return f
    }()

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Status bar
                if viewModel.isScanning {
                    HStack {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text(viewModel.scanProgress)
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 6)
                    .background(Color(.systemGray6))
                } else if let lastScan = viewModel.lastScanTime {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                            .font(.caption)
                        Text("Last scan: \(dateFormatter.string(from: lastScan))")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                        Text("\(viewModel.activities.count) results")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 6)
                    .background(Color(.systemGray6))
                }

                if viewModel.activities.isEmpty && !viewModel.isScanning {
                    if let error = viewModel.errorMessage {
                        ContentUnavailableView(
                            "Scanner",
                            systemImage: "antenna.radiowaves.left.and.right",
                            description: Text(error)
                        )
                    } else {
                        ContentUnavailableView(
                            "Unusual Activity Scanner",
                            systemImage: "antenna.radiowaves.left.and.right",
                            description: Text("Tap Scan to analyze your watchlist for unusual options activity.")
                        )
                    }
                } else {
                    List(viewModel.activities) { activity in
                        UnusualActivityRow(activity: activity)
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Scanner")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        Task { await viewModel.scan() }
                    } label: {
                        Label("Scan", systemImage: "magnifyingglass")
                    }
                    .disabled(viewModel.isScanning)
                }
            }
            .refreshable {
                await viewModel.scan()
            }
        }
    }
}

struct UnusualActivityRow: View {
    let activity: UnusualActivity

    private let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMM d"
        return f
    }()

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack {
                Text(activity.ticker)
                    .font(.headline)

                Text(activity.contract.contractType == .call ? "CALL" : "PUT")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(activity.contract.contractType == .call ? Color.green : Color.red)
                    .cornerRadius(4)

                Text("$\(activity.contract.strike, specifier: "%.2f")")
                    .font(.subheadline)

                Text(dateFormatter.string(from: activity.contract.expiration))
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                // Score badge
                Text(activity.scoreLabel)
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(scoreColor)
                    .cornerRadius(6)
            }

            // Stats
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 1) {
                    Text("Vol")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text(formatCompact(activity.contract.volume))
                        .font(.caption)
                        .monospacedDigit()
                }
                VStack(alignment: .leading, spacing: 1) {
                    Text("OI")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text(formatCompact(activity.contract.openInterest))
                        .font(.caption)
                        .monospacedDigit()
                }
                VStack(alignment: .leading, spacing: 1) {
                    Text("IV")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text(String(format: "%.1f%%", activity.contract.impliedVolatility * 100))
                        .font(.caption)
                        .monospacedDigit()
                }
                VStack(alignment: .leading, spacing: 1) {
                    Text("Price")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    Text(String(format: "$%.2f", activity.contract.lastPrice))
                        .font(.caption)
                        .monospacedDigit()
                }
            }

            // Reasons
            ForEach(activity.reasons, id: \.self) { reason in
                HStack(spacing: 4) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.caption2)
                        .foregroundColor(.orange)
                    Text(reason)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }

    private var scoreColor: Color {
        if activity.score >= 8.0 { return .red }
        if activity.score >= 5.0 { return .orange }
        return .blue
    }

    private func formatCompact(_ n: Int) -> String {
        if n >= 1_000_000 { return String(format: "%.1fM", Double(n) / 1_000_000) }
        if n >= 1_000 { return String(format: "%.1fK", Double(n) / 1_000) }
        return "\(n)"
    }
}
