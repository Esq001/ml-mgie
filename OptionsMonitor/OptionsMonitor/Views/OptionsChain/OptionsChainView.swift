import SwiftUI

struct OptionsChainView: View {
    @StateObject private var viewModel: OptionsChainViewModel

    init(ticker: String) {
        _viewModel = StateObject(wrappedValue: OptionsChainViewModel(ticker: ticker))
    }

    var body: some View {
        VStack(spacing: 0) {
            // Underlying price header
            if viewModel.underlyingPrice > 0 {
                HStack {
                    Text(viewModel.ticker)
                        .font(.title2)
                        .fontWeight(.bold)
                    Spacer()
                    Text("$\(viewModel.underlyingPrice, specifier: "%.2f")")
                        .font(.title2)
                        .monospacedDigit()
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
            }

            // Expiration picker
            if !viewModel.expirationDates.isEmpty {
                ExpirationPickerView(
                    dates: viewModel.expirationDates,
                    selectedDate: $viewModel.selectedExpiration
                )
                .onChange(of: viewModel.selectedExpiration) { _, newDate in
                    if let date = newDate {
                        Task { await viewModel.selectExpiration(date) }
                    }
                }
            }

            // Calls/Puts toggle
            Picker("Contract Type", selection: $viewModel.showCalls) {
                Text("Calls").tag(true)
                Text("Puts").tag(false)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)
            .padding(.vertical, 8)

            // Options list
            if viewModel.isLoading && viewModel.displayedContracts.isEmpty {
                Spacer()
                ProgressView("Loading options chain...")
                Spacer()
            } else if let error = viewModel.errorMessage {
                Spacer()
                ContentUnavailableView(
                    "Error",
                    systemImage: "exclamationmark.triangle",
                    description: Text(error)
                )
                Spacer()
            } else if viewModel.displayedContracts.isEmpty {
                Spacer()
                ContentUnavailableView(
                    "No Contracts",
                    systemImage: "doc.text",
                    description: Text("No options contracts available for this expiration.")
                )
                Spacer()
            } else {
                List(viewModel.displayedContracts) { contract in
                    NavigationLink {
                        OptionDetailView(
                            contract: contract,
                            ticker: viewModel.ticker,
                            underlyingPrice: viewModel.underlyingPrice
                        )
                    } label: {
                        OptionRowView(
                            contract: contract,
                            underlyingPrice: viewModel.underlyingPrice
                        )
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("Options Chain")
        .navigationBarTitleDisplayMode(.inline)
        .refreshable {
            await viewModel.refresh()
        }
        .task {
            await viewModel.loadChain()
        }
    }
}
