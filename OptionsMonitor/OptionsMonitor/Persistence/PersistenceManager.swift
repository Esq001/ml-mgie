import Foundation

final class PersistenceManager {
    static let shared = PersistenceManager()

    private let defaults = UserDefaults.standard

    private enum Keys {
        static let watchlist = "watchlist_tickers"
        static let alerts = "option_alerts"
    }

    private init() {}

    // MARK: - Watchlist

    func loadWatchlist() -> [String] {
        defaults.stringArray(forKey: Keys.watchlist) ?? ["AAPL", "TSLA", "SPY"]
    }

    func saveWatchlist(_ tickers: [String]) {
        defaults.set(tickers, forKey: Keys.watchlist)
    }

    func addTicker(_ ticker: String) {
        var list = loadWatchlist()
        let uppercased = ticker.uppercased()
        guard !list.contains(uppercased) else { return }
        list.append(uppercased)
        saveWatchlist(list)
    }

    func removeTicker(_ ticker: String) {
        var list = loadWatchlist()
        list.removeAll { $0 == ticker.uppercased() }
        saveWatchlist(list)
    }

    // MARK: - Alerts

    func loadAlerts() -> [OptionAlert] {
        guard let data = defaults.data(forKey: Keys.alerts) else { return [] }
        return (try? JSONDecoder().decode([OptionAlert].self, from: data)) ?? []
    }

    func saveAlerts(_ alerts: [OptionAlert]) {
        if let data = try? JSONEncoder().encode(alerts) {
            defaults.set(data, forKey: Keys.alerts)
        }
    }

    func addAlert(_ alert: OptionAlert) {
        var alerts = loadAlerts()
        alerts.append(alert)
        saveAlerts(alerts)
    }

    func removeAlert(id: UUID) {
        var alerts = loadAlerts()
        alerts.removeAll { $0.id == id }
        saveAlerts(alerts)
    }

    func toggleAlert(id: UUID) {
        var alerts = loadAlerts()
        if let index = alerts.firstIndex(where: { $0.id == id }) {
            alerts[index].isActive.toggle()
        }
        saveAlerts(alerts)
    }
}
