import Foundation

enum YahooFinanceError: LocalizedError {
    case invalidURL
    case networkError(Error)
    case decodingError(Error)
    case noData
    case apiError(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .networkError(let error): return "Network error: \(error.localizedDescription)"
        case .decodingError(let error): return "Data error: \(error.localizedDescription)"
        case .noData: return "No data available"
        case .apiError(let msg): return "API error: \(msg)"
        }
    }
}

actor YahooFinanceService {
    static let shared = YahooFinanceService()

    private let session: URLSession
    private let baseURL = "https://query1.finance.yahoo.com/v7/finance"

    private init() {
        let config = URLSessionConfiguration.default
        config.httpAdditionalHeaders = [
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
        ]
        config.timeoutIntervalForRequest = 15
        self.session = URLSession(configuration: config)
    }

    // MARK: - Fetch Options Chain

    func fetchOptionsChain(ticker: String, expirationDate: Date? = nil) async throws -> OptionsChain {
        var urlString = "\(baseURL)/options/\(ticker.uppercased())"
        if let expDate = expirationDate {
            let epoch = Int(expDate.timeIntervalSince1970)
            urlString += "?date=\(epoch)"
        }

        guard let url = URL(string: urlString) else {
            throw YahooFinanceError.invalidURL
        }

        let data: Data
        do {
            let (responseData, _) = try await session.data(from: url)
            data = responseData
        } catch {
            throw YahooFinanceError.networkError(error)
        }

        let response: YahooOptionsResponse
        do {
            let decoder = JSONDecoder()
            response = try decoder.decode(YahooOptionsResponse.self, from: data)
        } catch {
            throw YahooFinanceError.decodingError(error)
        }

        guard let result = response.optionChain.result?.first else {
            if let error = response.optionChain.error {
                throw YahooFinanceError.apiError(error.description ?? "Unknown error")
            }
            throw YahooFinanceError.noData
        }

        let underlyingPrice = result.quote?.regularMarketPrice ?? 0
        let symbol = result.underlyingSymbol ?? ticker.uppercased()

        let expirationDates = (result.expirationDates ?? []).map {
            Date(timeIntervalSince1970: TimeInterval($0))
        }

        let optionData = result.options?.first
        let calls = (optionData?.calls ?? []).map { mapContract($0, type: .call) }
        let puts = (optionData?.puts ?? []).map { mapContract($0, type: .put) }

        return OptionsChain(
            ticker: symbol,
            underlyingPrice: underlyingPrice,
            expirationDates: expirationDates,
            calls: calls,
            puts: puts
        )
    }

    // MARK: - Fetch Stock Quote

    func fetchQuote(ticker: String) async throws -> StockQuote {
        let urlString = "\(baseURL)/quote?symbols=\(ticker.uppercased())"

        guard let url = URL(string: urlString) else {
            throw YahooFinanceError.invalidURL
        }

        let data: Data
        do {
            let (responseData, _) = try await session.data(from: url)
            data = responseData
        } catch {
            throw YahooFinanceError.networkError(error)
        }

        let response: YahooQuoteResponse
        do {
            let decoder = JSONDecoder()
            response = try decoder.decode(YahooQuoteResponse.self, from: data)
        } catch {
            throw YahooFinanceError.decodingError(error)
        }

        guard let quoteData = response.quoteResponse?.result?.first else {
            throw YahooFinanceError.noData
        }

        return StockQuote(
            symbol: quoteData.symbol ?? ticker.uppercased(),
            name: quoteData.shortName ?? quoteData.longName ?? ticker.uppercased(),
            price: quoteData.regularMarketPrice ?? 0,
            change: quoteData.regularMarketChange ?? 0,
            changePercent: quoteData.regularMarketChangePercent ?? 0,
            marketCap: quoteData.marketCap
        )
    }

    // MARK: - Helpers

    private func mapContract(_ yahoo: YahooContract, type: ContractType) -> OptionContract {
        OptionContract(
            contractSymbol: yahoo.contractSymbol ?? "",
            strike: yahoo.strike ?? 0,
            lastPrice: yahoo.lastPrice ?? 0,
            bid: yahoo.bid ?? 0,
            ask: yahoo.ask ?? 0,
            volume: yahoo.volume ?? 0,
            openInterest: yahoo.openInterest ?? 0,
            impliedVolatility: yahoo.impliedVolatility ?? 0,
            expiration: Date(timeIntervalSince1970: TimeInterval(yahoo.expiration ?? 0)),
            contractType: type,
            lastTradeDate: yahoo.lastTradeDate.map { Date(timeIntervalSince1970: TimeInterval($0)) },
            change: yahoo.change ?? 0,
            percentChange: yahoo.percentChange ?? 0,
            inTheMoney: yahoo.inTheMoney ?? false
        )
    }
}
