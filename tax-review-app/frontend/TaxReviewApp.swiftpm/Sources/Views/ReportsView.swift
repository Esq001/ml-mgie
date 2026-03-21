import SwiftUI

struct ReportsView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedReviewIds: Set<String> = []
    @State private var includeDetails = true
    @State private var generatedReport = ""
    @State private var isGenerating = false
    private let api = APIService()

    var body: some View {
        HSplitView {
            // Review selection
            VStack(alignment: .leading, spacing: 12) {
                Text("Generate Report")
                    .font(.title3.bold())
                    .padding(.horizontal)
                    .padding(.top)

                if appState.reviews.isEmpty {
                    VStack(spacing: 8) {
                        Text("No reviews available")
                            .foregroundStyle(.secondary)
                        Text("Review some documents first")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(appState.reviews, selection: $selectedReviewIds) { review in
                        VStack(alignment: .leading) {
                            Text(review.entityName.isEmpty ? review.documentId : review.entityName)
                                .font(.headline)
                            Text("\(review.issues.count) issues")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                VStack(spacing: 8) {
                    Toggle("Include detailed issues", isOn: $includeDetails)

                    Button(action: generateReport) {
                        if isGenerating {
                            ProgressView()
                                .controlSize(.small)
                        } else {
                            Label("Generate Report", systemImage: "doc.richtext")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(selectedReviewIds.isEmpty || isGenerating)
                }
                .padding()
            }
            .frame(minWidth: 280, maxWidth: 350)

            // Report display
            if generatedReport.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "doc.richtext")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("Select reviews and generate a report")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                VStack(spacing: 0) {
                    HStack {
                        Text("Generated Report")
                            .font(.title2.bold())
                        Spacer()
                        Button("Copy") {
                            NSPasteboard.general.clearContents()
                            NSPasteboard.general.setString(generatedReport, forType: .string)
                        }
                        .buttonStyle(.bordered)
                    }
                    .padding()

                    Divider()

                    ScrollView {
                        Text(generatedReport)
                            .font(.system(.body, design: .monospaced))
                            .textSelection(.enabled)
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
    }

    private func generateReport() {
        Task {
            isGenerating = true
            defer { isGenerating = false }
            do {
                let request = ReportRequest(
                    reviewIds: Array(selectedReviewIds),
                    includeDetails: includeDetails,
                    reportFormat: "markdown"
                )
                let response = try await api.generateReport(
                    baseURL: appState.serverURL, request: request
                )
                generatedReport = response.report
            } catch {
                appState.errorMessage = "Report generation failed: \(error.localizedDescription)"
            }
        }
    }
}
