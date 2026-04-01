import SwiftUI

struct AddTickerView: View {
    @ObservedObject var viewModel: WatchlistViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var tickerText = ""
    @FocusState private var isFocused: Bool

    private let popularTickers = [
        "SPY", "QQQ", "AAPL", "TSLA", "NVDA",
        "AMZN", "META", "MSFT", "GOOGL", "AMD",
        "IWM", "DIA", "XLF", "GLD", "TLT"
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                // Text input
                HStack {
                    TextField("Enter ticker symbol", text: $tickerText)
                        .textFieldStyle(.roundedBorder)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                        .focused($isFocused)
                        .onSubmit {
                            addAndDismiss()
                        }

                    Button("Add") {
                        addAndDismiss()
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(tickerText.trimmingCharacters(in: .whitespaces).isEmpty)
                }
                .padding(.horizontal)

                // Popular tickers
                VStack(alignment: .leading, spacing: 8) {
                    Text("Popular")
                        .font(.headline)
                        .padding(.horizontal)

                    LazyVGrid(columns: [
                        GridItem(.adaptive(minimum: 70))
                    ], spacing: 8) {
                        ForEach(popularTickers, id: \.self) { ticker in
                            Button(ticker) {
                                viewModel.addTicker(ticker)
                                dismiss()
                            }
                            .buttonStyle(.bordered)
                            .disabled(viewModel.tickers.contains(ticker))
                        }
                    }
                    .padding(.horizontal)
                }

                Spacer()
            }
            .padding(.top)
            .navigationTitle("Add Ticker")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .onAppear {
                isFocused = true
            }
        }
    }

    private func addAndDismiss() {
        let ticker = tickerText.trimmingCharacters(in: .whitespaces)
        guard !ticker.isEmpty else { return }
        viewModel.addTicker(ticker)
        dismiss()
    }
}
