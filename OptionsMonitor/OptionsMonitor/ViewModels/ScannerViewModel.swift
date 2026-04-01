import Foundation

@MainActor
final class ScannerViewModel: ObservableObject {
    @Published var activities: [UnusualActivity] = []
    @Published var isScanning = false
    @Published var lastScanTime: Date?
    @Published var errorMessage: String?
    @Published var scanProgress: String = ""

    private let yahooService = YahooFinanceService.shared
    private let persistence = PersistenceManager.shared
    private var refreshTimer: Timer?

    func scan() async {
        isScanning = true
        errorMessage = nil
        activities = []

        let tickers = persistence.loadWatchlist()
        guard !tickers.isEmpty else {
            errorMessage = "Add tickers to your watchlist to scan for unusual activity."
            isScanning = false
            return
        }

        var allChains: [OptionsChain] = []

        for (index, ticker) in tickers.enumerated() {
            scanProgress = "Scanning \(ticker) (\(index + 1)/\(tickers.count))..."

            do {
                let chain = try await yahooService.fetchOptionsChain(ticker: ticker)
                allChains.append(chain)
            } catch {
                // Skip tickers that fail
                continue
            }
        }

        activities = UnusualActivityService.scanMultiple(chains: allChains, minScore: 3.0)
        lastScanTime = Date()
        scanProgress = ""
        isScanning = false
    }

    func startAutoScan(interval: TimeInterval = 60) {
        stopAutoScan()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.scan()
            }
        }
    }

    func stopAutoScan() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }
}
