import Foundation

struct StockQuote: Identifiable {
    var id: String { symbol }

    let symbol: String
    let name: String
    let price: Double
    let change: Double
    let changePercent: Double
    let marketCap: Int64?

    var isPositive: Bool {
        change >= 0
    }

    var formattedPrice: String {
        String(format: "$%.2f", price)
    }

    var formattedChange: String {
        let sign = change >= 0 ? "+" : ""
        return String(format: "%@%.2f (%.2f%%)", sign, change, changePercent)
    }
}
