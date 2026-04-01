import Foundation
import UserNotifications

actor AlertService {
    static let shared = AlertService()

    private var hasRequestedPermission = false

    private init() {}

    /// Request notification permissions
    func requestPermissions() async {
        guard !hasRequestedPermission else { return }
        hasRequestedPermission = true

        let center = UNUserNotificationCenter.current()
        _ = try? await center.requestAuthorization(options: [.alert, .sound, .badge])
    }

    /// Evaluate all active alerts against current option data
    func evaluateAlerts(
        alerts: [OptionAlert],
        contracts: [OptionContract],
        underlyingPrice: Double
    ) async -> [OptionAlert] {
        var triggeredAlerts: [OptionAlert] = []

        for alert in alerts where alert.isActive {
            guard let contract = contracts.first(where: { $0.contractSymbol == alert.contractSymbol }) else {
                continue
            }

            let currentValue: Double
            switch alert.alertType {
            case .price:
                currentValue = contract.lastPrice
            case .impliedVolatility:
                currentValue = contract.impliedVolatility
            case .delta:
                currentValue = contract.delta ?? 0
            case .volume:
                currentValue = Double(contract.volume)
            }

            let isTriggered: Bool
            switch alert.condition {
            case .above:
                isTriggered = currentValue >= alert.targetValue
            case .below:
                isTriggered = currentValue <= alert.targetValue
            }

            if isTriggered {
                triggeredAlerts.append(alert)
                await sendNotification(for: alert, currentValue: currentValue)
            }
        }

        return triggeredAlerts
    }

    /// Send a local notification for a triggered alert
    private func sendNotification(for alert: OptionAlert, currentValue: Double) async {
        let center = UNUserNotificationCenter.current()

        let content = UNMutableNotificationContent()
        content.title = "Options Alert: \(alert.ticker)"
        content.body = "\(alert.displayDescription) — Current: \(formatValue(currentValue, type: alert.alertType))"
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: alert.id.uuidString,
            content: content,
            trigger: nil // Deliver immediately
        )

        try? await center.add(request)
    }

    private func formatValue(_ value: Double, type: AlertType) -> String {
        switch type {
        case .price:
            return String(format: "$%.2f", value)
        case .impliedVolatility:
            return String(format: "%.1f%%", value * 100)
        case .delta:
            return String(format: "%.3f", value)
        case .volume:
            return String(format: "%.0f", value)
        }
    }
}
