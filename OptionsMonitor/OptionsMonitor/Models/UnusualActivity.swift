import Foundation

struct UnusualActivity: Identifiable {
    let id = UUID()
    let contract: OptionContract
    let ticker: String
    let underlyingPrice: Double
    let score: Double
    let reasons: [String]
    let detectedAt: Date

    var scoreLabel: String {
        if score >= 8.0 { return "Very High" }
        if score >= 5.0 { return "High" }
        if score >= 3.0 { return "Moderate" }
        return "Low"
    }
}
