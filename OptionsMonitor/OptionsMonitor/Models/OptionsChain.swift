import Foundation

struct OptionsChain {
    let ticker: String
    let underlyingPrice: Double
    let expirationDates: [Date]
    let calls: [OptionContract]
    let puts: [OptionContract]
}

// MARK: - Yahoo Finance API Response Models

struct YahooOptionsResponse: Codable {
    let optionChain: YahooOptionChain
}

struct YahooOptionChain: Codable {
    let result: [YahooOptionResult]?
    let error: YahooError?
}

struct YahooError: Codable {
    let code: String?
    let description: String?
}

struct YahooOptionResult: Codable {
    let underlyingSymbol: String?
    let expirationDates: [Int]?
    let strikes: [Double]?
    let hasMiniOptions: Bool?
    let quote: YahooQuoteData?
    let options: [YahooOptionData]?
}

struct YahooQuoteData: Codable {
    let symbol: String?
    let regularMarketPrice: Double?
    let regularMarketChange: Double?
    let regularMarketChangePercent: Double?
    let shortName: String?
    let longName: String?
    let marketCap: Int64?
}

struct YahooOptionData: Codable {
    let expirationDate: Int?
    let hasMiniOptions: Bool?
    let calls: [YahooContract]?
    let puts: [YahooContract]?
}

struct YahooContract: Codable {
    let contractSymbol: String?
    let strike: Double?
    let currency: String?
    let lastPrice: Double?
    let change: Double?
    let percentChange: Double?
    let volume: Int?
    let openInterest: Int?
    let bid: Double?
    let ask: Double?
    let contractSize: String?
    let expiration: Int?
    let lastTradeDate: Int?
    let impliedVolatility: Double?
    let inTheMoney: Bool?
}

// MARK: - Yahoo Finance Quote Response

struct YahooQuoteResponse: Codable {
    let quoteResponse: YahooQuoteResponseBody?
}

struct YahooQuoteResponseBody: Codable {
    let result: [YahooQuoteData]?
    let error: YahooError?
}
