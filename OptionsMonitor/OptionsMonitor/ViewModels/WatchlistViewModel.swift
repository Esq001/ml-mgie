import Foundation

@MainActor
final class WatchlistViewModel: ObservableObject {
    @Published var tickers: [String] = []
    @Published var quotes: [String: StockQuote] = [:]
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let persistence = PersistenceManager.shared
    private let yahooService = YahooFinanceService.shared
    private var refreshTimer: Timer?

    init() {
        tickers = persistence.loadWatchlist()
    }

    func loadQuotes() async {
        isLoading = true
        errorMessage = nil

        await withTaskGroup(of: (String, StockQuote?).self) { group in
            for ticker in tickers {
                group.addTask {
                    let quote = try? await self.yahooService.fetchQuote(ticker: ticker)
                    return (ticker, quote)
                }
            }

            for await (ticker, quote) in group {
                if let quote = quote {
                    quotes[ticker] = quote
                }
            }
        }

        isLoading = false
    }

    func addTicker(_ ticker: String) {
        let uppercased = ticker.uppercased().trimmingCharacters(in: .whitespacesAndNewlines)
        guard !uppercased.isEmpty, !tickers.contains(uppercased) else { return }
        tickers.append(uppercased)
        persistence.saveWatchlist(tickers)

        Task {
            if let quote = try? await yahooService.fetchQuote(ticker: uppercased) {
                quotes[uppercased] = quote
            }
        }
    }

    func removeTicker(_ ticker: String) {
        tickers.removeAll { $0 == ticker }
        quotes.removeValue(forKey: ticker)
        persistence.saveWatchlist(tickers)
    }

    func removeTickers(at offsets: IndexSet) {
        let tickersToRemove = offsets.map { tickers[$0] }
        tickers.remove(atOffsets: offsets)
        for t in tickersToRemove {
            quotes.removeValue(forKey: t)
        }
        persistence.saveWatchlist(tickers)
    }

    func startAutoRefresh(interval: TimeInterval = 60) {
        stopAutoRefresh()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.loadQuotes()
            }
        }
    }

    func stopAutoRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }
}
