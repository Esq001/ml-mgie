import SwiftUI

struct CreateAlertView: View {
    let contract: OptionContract
    let ticker: String
    @ObservedObject var alertsViewModel: AlertsViewModel

    @Environment(\.dismiss) private var dismiss

    @State private var alertType: AlertType = .price
    @State private var condition: AlertCondition = .above
    @State private var targetValueText: String = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Contract") {
                    LabeledContent("Ticker", value: ticker)
                    LabeledContent("Strike", value: String(format: "$%.2f", contract.strike))
                    LabeledContent("Type", value: contract.contractType == .call ? "Call" : "Put")
                    LabeledContent("Current Price", value: String(format: "$%.2f", contract.lastPrice))
                    LabeledContent("IV", value: String(format: "%.1f%%", contract.impliedVolatility * 100))
                }

                Section("Alert Settings") {
                    Picker("Alert Type", selection: $alertType) {
                        ForEach(AlertType.allCases, id: \.self) { type in
                            Text(type.rawValue).tag(type)
                        }
                    }

                    Picker("Condition", selection: $condition) {
                        ForEach(AlertCondition.allCases, id: \.self) { cond in
                            Text(cond.rawValue).tag(cond)
                        }
                    }

                    HStack {
                        Text("Target Value")
                        Spacer()
                        TextField("Value", text: $targetValueText)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                            .frame(width: 120)
                        Text(alertType.unit)
                            .foregroundColor(.secondary)
                    }
                }

                Section {
                    Text(previewText)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                } header: {
                    Text("Preview")
                }
            }
            .navigationTitle("Create Alert")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        saveAlert()
                    }
                    .disabled(targetValue == nil)
                }
            }
            .onAppear {
                setDefaultTarget()
            }
            .onChange(of: alertType) { _, _ in
                setDefaultTarget()
            }
        }
    }

    private var targetValue: Double? {
        Double(targetValueText)
    }

    private var previewText: String {
        guard let value = targetValue else {
            return "Enter a target value"
        }

        let condText = condition.rawValue.lowercased()
        switch alertType {
        case .price:
            return "Alert when price goes \(condText) $\(String(format: "%.2f", value))"
        case .impliedVolatility:
            return "Alert when IV goes \(condText) \(String(format: "%.1f", value))%"
        case .delta:
            return "Alert when delta goes \(condText) \(String(format: "%.3f", value))"
        case .volume:
            return "Alert when volume goes \(condText) \(String(format: "%.0f", value))"
        }
    }

    private func setDefaultTarget() {
        switch alertType {
        case .price:
            targetValueText = String(format: "%.2f", contract.lastPrice)
        case .impliedVolatility:
            targetValueText = String(format: "%.1f", contract.impliedVolatility * 100)
        case .delta:
            targetValueText = String(format: "%.3f", contract.delta ?? 0.5)
        case .volume:
            targetValueText = "\(contract.volume)"
        }
    }

    private func saveAlert() {
        guard let value = targetValue else { return }

        // For IV, convert percentage input to decimal
        let adjustedValue: Double
        if alertType == .impliedVolatility {
            adjustedValue = value / 100.0
        } else {
            adjustedValue = value
        }

        let alert = OptionAlert(
            contractSymbol: contract.contractSymbol,
            ticker: ticker,
            strikePrice: contract.strike,
            contractType: contract.contractType,
            alertType: alertType,
            condition: condition,
            targetValue: adjustedValue
        )

        alertsViewModel.addAlert(alert)
        dismiss()
    }
}
