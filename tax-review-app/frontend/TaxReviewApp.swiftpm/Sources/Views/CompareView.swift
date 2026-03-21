import SwiftUI

struct CompareView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedDocIds: Set<String> = []
    @State private var comparisonFocus = ""
    @State private var comparisonResult: ComparisonResult?
    @State private var isComparing = false
    private let api = APIService()

    var body: some View {
        HSplitView {
            // Document selection
            VStack(alignment: .leading, spacing: 12) {
                Text("Select Documents to Compare")
                    .font(.title3.bold())
                    .padding(.horizontal)
                    .padding(.top)

                List(appState.documents, selection: $selectedDocIds) { doc in
                    Label(doc.filename, systemImage: "doc")
                }

                VStack(spacing: 8) {
                    TextField("Comparison focus (optional)", text: $comparisonFocus)
                        .textFieldStyle(.roundedBorder)

                    Button(action: compare) {
                        if isComparing {
                            ProgressView()
                                .controlSize(.small)
                        } else {
                            Label("Compare Selected", systemImage: "arrow.left.arrow.right")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(selectedDocIds.count < 2 || isComparing)
                }
                .padding()
            }
            .frame(minWidth: 280, maxWidth: 350)

            // Results
            if let result = comparisonResult {
                comparisonDetail(result)
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "arrow.left.arrow.right")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("Select 2+ documents and compare")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private func comparisonDetail(_ result: ComparisonResult) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Comparison Results")
                    .font(.title2.bold())

                // Summary
                VStack(alignment: .leading, spacing: 8) {
                    Text("Summary")
                        .font(.title3.bold())
                    Text(result.summary)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .background(.secondary.opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: 12))

                // Discrepancies
                if !result.discrepancies.isEmpty {
                    Text("Discrepancies (\(result.discrepancies.count))")
                        .font(.title3.bold())
                    ForEach(result.discrepancies) { issue in
                        IssueCard(issue: issue) {}
                    }
                }

                // Reconciliation notes
                if !result.reconciliationNotes.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Reconciliation Notes")
                            .font(.title3.bold())
                        ForEach(result.reconciliationNotes, id: \.self) { note in
                            HStack(alignment: .top, spacing: 8) {
                                Image(systemName: "note.text")
                                    .foregroundStyle(.blue)
                                Text(note)
                            }
                        }
                    }
                }
            }
            .padding()
        }
    }

    private func compare() {
        Task {
            isComparing = true
            defer { isComparing = false }
            do {
                let request = CompareRequest(
                    documentIds: Array(selectedDocIds),
                    comparisonFocus: comparisonFocus
                )
                comparisonResult = try await api.compareDocuments(
                    baseURL: appState.serverURL, request: request
                )
                if let result = comparisonResult {
                    appState.comparisons.append(result)
                }
            } catch {
                appState.errorMessage = "Comparison failed: \(error.localizedDescription)"
            }
        }
    }
}
