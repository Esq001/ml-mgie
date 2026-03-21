import SwiftUI

struct CompareView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedDocIds: Set<String> = []
    @State private var comparisonFocus = ""
    @State private var comparisonResult: ComparisonResult?
    @State private var isComparing = false
    @State private var showSideBySide = true
    private let api = APIService()

    private var selectedDocs: [TaxDocument] {
        appState.documents.filter { selectedDocIds.contains($0.id) }
    }

    var body: some View {
        HSplitView {
            // Left: Document selection panel
            selectionPanel
                .frame(minWidth: 250, maxWidth: 300)

            // Right: Side-by-side or results
            if let result = comparisonResult {
                VStack(spacing: 0) {
                    // Toggle bar
                    HStack {
                        Picker("View", selection: $showSideBySide) {
                            Text("Side by Side").tag(true)
                            Text("Results Only").tag(false)
                        }
                        .pickerStyle(.segmented)
                        .frame(width: 240)
                        Spacer()
                        Text("\(result.discrepancies.count) discrepancies found")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                    .background(.bar)

                    Divider()

                    if showSideBySide {
                        sideBySideView(result)
                    } else {
                        resultsOnlyView(result)
                    }
                }
            } else if selectedDocIds.count >= 2 && !isComparing {
                // Preview side-by-side before comparison
                sideBySidePreview
            } else {
                emptyState
            }
        }
    }

    // MARK: - Selection Panel

    private var selectionPanel: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Image(systemName: "arrow.left.arrow.right")
                    .foregroundStyle(.blue)
                Text("Compare")
                    .font(.headline)
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.bar)

            Divider()

            List(appState.documents, selection: $selectedDocIds) { doc in
                HStack(spacing: 10) {
                    Image(systemName: docIcon(doc))
                        .foregroundStyle(docColor(doc))
                        .frame(width: 20)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(doc.filename)
                            .font(.callout)
                            .lineLimit(1)
                        Text(doc.documentType.displayName)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 2)
            }

            Divider()

            VStack(spacing: 10) {
                TextField("Focus area (optional)", text: $comparisonFocus)
                    .textFieldStyle(.roundedBorder)
                    .font(.callout)

                Button(action: compare) {
                    HStack(spacing: 6) {
                        if isComparing {
                            ProgressView()
                                .controlSize(.small)
                            Text("Comparing...")
                        } else {
                            Image(systemName: "sparkles")
                            Text("Compare with Claude")
                        }
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(selectedDocIds.count < 2 || isComparing)
                .controlSize(.large)

                if selectedDocIds.count < 2 {
                    Text("Select at least 2 documents")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
            }
            .padding()
        }
    }

    // MARK: - Side by Side View

    private func sideBySideView(_ result: ComparisonResult) -> some View {
        VStack(spacing: 0) {
            // Document panels
            HSplitView {
                ForEach(Array(selectedDocs.prefix(2).enumerated()), id: \.element.id) { index, doc in
                    VStack(spacing: 0) {
                        // Document header
                        HStack {
                            Circle()
                                .fill(index == 0 ? Color.blue : Color.purple)
                                .frame(width: 8, height: 8)
                            Text(doc.filename)
                                .font(.subheadline.bold())
                            Spacer()
                            Text(doc.documentType.displayName)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(10)
                        .background(
                            (index == 0 ? Color.blue : Color.purple).opacity(0.05)
                        )

                        Divider()

                        // Document content
                        ScrollView {
                            Text(cleanText(doc.extractedText))
                                .font(.system(.caption, design: .monospaced))
                                .textSelection(.enabled)
                                .padding(10)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }
            }
            .frame(minHeight: 300)

            Divider()

            // Discrepancies panel at bottom
            discrepanciesPanel(result)
                .frame(minHeight: 200, maxHeight: 350)
        }
    }

    private func discrepanciesPanel(_ result: ComparisonResult) -> some View {
        VStack(spacing: 0) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                Text("Discrepancies & Findings")
                    .font(.headline)
                Spacer()
            }
            .padding(10)
            .background(.bar)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    // Summary
                    if !result.summary.isEmpty {
                        Text(result.summary)
                            .font(.callout)
                            .foregroundStyle(.secondary)
                            .padding(10)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(.secondary.opacity(0.04))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }

                    // Discrepancies
                    ForEach(result.discrepancies) { issue in
                        HStack(alignment: .top, spacing: 10) {
                            Circle()
                                .fill(severityColor(issue.severity))
                                .frame(width: 10, height: 10)
                                .padding(.top, 4)

                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(issue.title)
                                        .font(.callout.bold())
                                    Spacer()
                                    Text(issue.severity.rawValue.uppercased())
                                        .font(.caption2.bold())
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(severityColor(issue.severity).opacity(0.12))
                                        .foregroundStyle(severityColor(issue.severity))
                                        .clipShape(Capsule())
                                }
                                Text(issue.description)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                if !issue.recommendation.isEmpty {
                                    HStack(alignment: .top, spacing: 4) {
                                        Image(systemName: "lightbulb.fill")
                                            .foregroundStyle(.yellow)
                                            .font(.caption2)
                                        Text(issue.recommendation)
                                            .font(.caption)
                                            .italic()
                                    }
                                    .padding(6)
                                    .background(.yellow.opacity(0.05))
                                    .clipShape(RoundedRectangle(cornerRadius: 4))
                                }
                            }
                        }
                        .padding(10)
                        .background(.background)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                        .shadow(color: .black.opacity(0.03), radius: 2, y: 1)
                    }

                    // Reconciliation notes
                    if !result.reconciliationNotes.isEmpty {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Reconciliation Notes")
                                .font(.subheadline.bold())
                            ForEach(result.reconciliationNotes, id: \.self) { note in
                                HStack(alignment: .top, spacing: 6) {
                                    Image(systemName: "checkmark.diamond.fill")
                                        .foregroundStyle(.mint)
                                        .font(.caption)
                                    Text(note)
                                        .font(.caption)
                                }
                            }
                        }
                        .padding(10)
                        .background(.mint.opacity(0.04))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
                .padding(12)
            }
        }
    }

    // MARK: - Side by Side Preview (before comparison)

    private var sideBySidePreview: some View {
        HSplitView {
            ForEach(Array(selectedDocs.prefix(2).enumerated()), id: \.element.id) { index, doc in
                VStack(spacing: 0) {
                    HStack {
                        Circle()
                            .fill(index == 0 ? Color.blue : Color.purple)
                            .frame(width: 8, height: 8)
                        Text(doc.filename)
                            .font(.subheadline.bold())
                        Spacer()
                    }
                    .padding(10)
                    .background((index == 0 ? Color.blue : Color.purple).opacity(0.05))

                    Divider()

                    ScrollView {
                        Text(cleanText(doc.extractedText))
                            .font(.system(.caption, design: .monospaced))
                            .textSelection(.enabled)
                            .padding(10)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
    }

    // MARK: - Results Only View

    private func resultsOnlyView(_ result: ComparisonResult) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Summary card
                VStack(alignment: .leading, spacing: 8) {
                    Text("Summary")
                        .font(.title3.bold())
                    Text(result.summary)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
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

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "arrow.left.arrow.right.circle")
                .font(.system(size: 56))
                .foregroundStyle(.secondary.opacity(0.5))
            Text("Compare Tax Documents")
                .font(.title3.bold())
                .foregroundStyle(.secondary)
            Text("Select two or more documents from the list\nto compare side by side and find discrepancies")
                .font(.callout)
                .foregroundStyle(.tertiary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Helpers

    private func severityColor(_ severity: IssueSeverity) -> Color {
        switch severity {
        case .high: return .red
        case .medium: return .orange
        case .low: return .yellow
        case .info: return .blue
        }
    }

    private func docIcon(_ doc: TaxDocument) -> String {
        switch doc.fileType {
        case "pdf": return "doc.fill"
        case "excel": return "tablecells.fill"
        case "csv": return "tablecells"
        case "image": return "photo.fill"
        default: return "doc"
        }
    }

    private func docColor(_ doc: TaxDocument) -> Color {
        switch doc.documentType {
        case .taxReturn: return .blue
        case .workPaper: return .green
        case .schedule: return .purple
        case .supportingDoc: return .orange
        case .other: return .gray
        }
    }

    private func cleanText(_ text: String) -> String {
        // Strip base64 image blocks for display
        text.replacingOccurrences(
            of: "\\[IMAGE:data:image/[^\\]]+\\]",
            with: "[scanned page]",
            options: .regularExpression
        )
    }

    // MARK: - Actions

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
