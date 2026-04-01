import SwiftUI

struct WatchlistView: View {
    @StateObject private var viewModel = WatchlistViewModel()
    @State private var showAddTicker = false

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.tickers.isEmpty {
                    ContentUnavailableView(
                        "No Tickers",
                        systemImage: "plus.circle",
                        description: Text("Add tickers to your watchlist to monitor options.")
                    )
                } else {
                    List {
                        ForEach(viewModel.tickers, id: \.self) { ticker in
                            NavigationLink(value: ticker) {
                                WatchlistRow(
                                    ticker: ticker,
                                    quote: viewModel.quotes[ticker]
                                )
                            }
                        }
                        .onDelete { offsets in
                            viewModel.removeTickers(at: offsets)
                        }
                    }
                    .refreshable {
                        await viewModel.loadQuotes()
                    }
                }
            }
            .navigationTitle("Watchlist")
            .navigationDestination(for: String.self) { ticker in
                OptionsChainView(ticker: ticker)
            }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showAddTicker = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showAddTicker) {
                AddTickerView(viewModel: viewModel)
            }
            .task {
                await viewModel.loadQuotes()
                viewModel.startAutoRefresh()
            }
            .onDisappear {
                viewModel.stopAutoRefresh()
            }
        }
    }
}

struct WatchlistRow: View {
    let ticker: String
    let quote: StockQuote?

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(ticker)
                    .font(.headline)
                if let name = quote?.name {
                    Text(name)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer()

            if let quote = quote {
                VStack(alignment: .trailing, spacing: 2) {
                    Text(quote.formattedPrice)
                        .font(.headline)
                        .monospacedDigit()
                    Text(quote.formattedChange)
                        .font(.caption)
                        .foregroundColor(quote.isPositive ? .green : .red)
                        .monospacedDigit()
                }
            } else {
                ProgressView()
            }
        }
        .padding(.vertical, 4)
    }
}
