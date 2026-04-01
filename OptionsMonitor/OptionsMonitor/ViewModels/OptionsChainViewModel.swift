import Foundation

@MainActor
final class OptionsChainViewModel: ObservableObject {
    @Published var chain: OptionsChain?
    @Published var calls: [OptionContract] = []
    @Published var puts: [OptionContract] = []
    @Published var expirationDates: [Date] = []
    @Published var selectedExpiration: Date?
    @Published var showCalls = true
    @Published var isLoading = false
    @Published var errorMessage: String?

    let ticker: String
    private let yahooService = YahooFinanceService.shared

    var displayedContracts: [OptionContract] {
        showCalls ? calls : puts
    }

    var underlyingPrice: Double {
        chain?.underlyingPrice ?? 0
    }

    init(ticker: String) {
        self.ticker = ticker
    }

    func loadChain() async {
        isLoading = true
        errorMessage = nil

        do {
            let result = try await yahooService.fetchOptionsChain(
                ticker: ticker,
                expirationDate: selectedExpiration
            )

            chain = result
            expirationDates = result.expirationDates

            if selectedExpiration == nil {
                selectedExpiration = result.expirationDates.first
            }

            // Calculate Greeks for all contracts
            calls = BlackScholesService.calculateGreeks(
                for: result.calls,
                underlyingPrice: result.underlyingPrice
            )
            puts = BlackScholesService.calculateGreeks(
                for: result.puts,
                underlyingPrice: result.underlyingPrice
            )

            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func selectExpiration(_ date: Date) async {
        selectedExpiration = date
        await loadChain()
    }

    func refresh() async {
        await loadChain()
    }
}
