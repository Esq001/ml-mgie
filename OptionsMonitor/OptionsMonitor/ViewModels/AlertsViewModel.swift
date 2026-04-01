import Foundation

@MainActor
final class AlertsViewModel: ObservableObject {
    @Published var alerts: [OptionAlert] = []
    @Published var isLoading = false

    private let persistence = PersistenceManager.shared
    private let alertService = AlertService.shared
    private let yahooService = YahooFinanceService.shared

    init() {
        alerts = persistence.loadAlerts()
    }

    func addAlert(_ alert: OptionAlert) {
        alerts.append(alert)
        persistence.saveAlerts(alerts)

        Task {
            await alertService.requestPermissions()
        }
    }

    func removeAlert(at offsets: IndexSet) {
        alerts.remove(atOffsets: offsets)
        persistence.saveAlerts(alerts)
    }

    func removeAlert(id: UUID) {
        alerts.removeAll { $0.id == id }
        persistence.saveAlerts(alerts)
    }

    func toggleAlert(id: UUID) {
        if let index = alerts.firstIndex(where: { $0.id == id }) {
            alerts[index].isActive.toggle()
        }
        persistence.saveAlerts(alerts)
    }

    /// Check all active alerts against live data
    func evaluateAlerts() async {
        isLoading = true

        // Group alerts by ticker to minimize API calls
        let tickerGroups = Dictionary(grouping: alerts.filter(\.isActive)) { $0.ticker }

        for (ticker, tickerAlerts) in tickerGroups {
            do {
                let chain = try await yahooService.fetchOptionsChain(ticker: ticker)
                let allContracts = chain.calls + chain.puts
                let contractsWithGreeks = BlackScholesService.calculateGreeks(
                    for: allContracts,
                    underlyingPrice: chain.underlyingPrice
                )

                let triggered = await alertService.evaluateAlerts(
                    alerts: tickerAlerts,
                    contracts: contractsWithGreeks,
                    underlyingPrice: chain.underlyingPrice
                )

                // Deactivate triggered alerts
                for triggeredAlert in triggered {
                    if let index = alerts.firstIndex(where: { $0.id == triggeredAlert.id }) {
                        alerts[index].isActive = false
                    }
                }
            } catch {
                // Skip tickers that fail to load
                continue
            }
        }

        persistence.saveAlerts(alerts)
        isLoading = false
    }
}
