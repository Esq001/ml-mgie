import Foundation

enum AlertType: String, Codable, CaseIterable {
    case price = "Price"
    case impliedVolatility = "IV"
    case delta = "Delta"
    case volume = "Volume"

    var unit: String {
        switch self {
        case .price: return "$"
        case .impliedVolatility: return "%"
        case .delta: return ""
        case .volume: return ""
        }
    }
}

enum AlertCondition: String, Codable, CaseIterable {
    case above = "Above"
    case below = "Below"
}

struct OptionAlert: Identifiable, Codable {
    let id: UUID
    let contractSymbol: String
    let ticker: String
    let strikePrice: Double
    let contractType: ContractType
    let alertType: AlertType
    let condition: AlertCondition
    let targetValue: Double
    var isActive: Bool
    let createdAt: Date

    var displayDescription: String {
        let typeLabel = alertType.rawValue
        let condLabel = condition.rawValue.lowercased()
        let valueStr: String
        switch alertType {
        case .price:
            valueStr = String(format: "$%.2f", targetValue)
        case .impliedVolatility:
            valueStr = String(format: "%.1f%%", targetValue * 100)
        case .delta:
            valueStr = String(format: "%.3f", targetValue)
        case .volume:
            valueStr = String(format: "%.0f", targetValue)
        }
        return "\(ticker) $\(String(format: "%.0f", strikePrice)) \(contractType.rawValue.capitalized) — \(typeLabel) \(condLabel) \(valueStr)"
    }

    init(
        id: UUID = UUID(),
        contractSymbol: String,
        ticker: String,
        strikePrice: Double,
        contractType: ContractType,
        alertType: AlertType,
        condition: AlertCondition,
        targetValue: Double,
        isActive: Bool = true,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.contractSymbol = contractSymbol
        self.ticker = ticker
        self.strikePrice = strikePrice
        self.contractType = contractType
        self.alertType = alertType
        self.condition = condition
        self.targetValue = targetValue
        self.isActive = isActive
        self.createdAt = createdAt
    }
}
