import Foundation

enum ContractType: String, Codable {
    case call
    case put
}

struct OptionContract: Identifiable, Codable {
    var id: String { contractSymbol }

    let contractSymbol: String
    let strike: Double
    let lastPrice: Double
    let bid: Double
    let ask: Double
    let volume: Int
    let openInterest: Int
    let impliedVolatility: Double
    let expiration: Date
    let contractType: ContractType
    let lastTradeDate: Date?
    let change: Double
    let percentChange: Double
    let inTheMoney: Bool

    // Greeks (computed locally via Black-Scholes)
    var delta: Double?
    var gamma: Double?
    var theta: Double?
    var vega: Double?

    var midPrice: Double {
        (bid + ask) / 2.0
    }

    var spread: Double {
        ask - bid
    }

    var volumeToOIRatio: Double {
        guard openInterest > 0 else { return 0 }
        return Double(volume) / Double(openInterest)
    }
}
