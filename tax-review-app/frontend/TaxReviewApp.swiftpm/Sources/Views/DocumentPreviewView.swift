import SwiftUI
import PDFKit
import QuickLook

struct DocumentPreviewView: View {
    let document: TaxDocument
    @EnvironmentObject var appState: AppState
    @State private var showReviewPanel = true
    @State private var reviewFocus: [String] = []
    @State private var customInstructions = ""
    @State private var isReviewing = false
    private let api = APIService()

    private var review: ReviewResult? {
        appState.reviewForDocument(document.id)
    }

    var body: some View {
        HSplitView {
            // Document preview panel
            documentPanel
                .frame(minWidth: 500)

            // Review / info panel
            if showReviewPanel {
                reviewPanel
                    .frame(minWidth: 350, maxWidth: 500)
            }
        }
        .toolbar {
            ToolbarItem {
                Button {
                    withAnimation(.easeInOut(duration: 0.25)) {
                        showReviewPanel.toggle()
                    }
                } label: {
                    Image(systemName: showReviewPanel ? "sidebar.trailing" : "sidebar.trailing")
                }
            }
        }
    }

    // MARK: - Document Panel

    private var documentPanel: some View {
        VStack(spacing: 0) {
            // Document header
            HStack {
                Image(systemName: iconForType)
                    .font(.title2)
                    .foregroundStyle(colorForType)
                VStack(alignment: .leading, spacing: 2) {
                    Text(document.filename)
                        .font(.headline)
                    HStack(spacing: 8) {
                        Text(document.documentType.displayName)
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(colorForType.opacity(0.1))
                            .foregroundStyle(colorForType)
                            .clipShape(Capsule())
                        Text(document.fileSizeFormatted)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        if let pages = document.pageCount {
                            Text("\(pages) pages")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                Spacer()
            }
            .padding()
            .background(.bar)

            Divider()

            // Content area
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    switch document.fileType {
                    case "pdf":
                        pdfPreview
                    case "excel", "csv":
                        spreadsheetPreview
                    case "image":
                        imagePreview
                    default:
                        textPreview
                    }
                }
                .padding()
            }
        }
    }

    private var pdfPreview: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Show extracted text with page separators styled nicely
            ForEach(extractedPages, id: \.self) { page in
                VStack(alignment: .leading, spacing: 8) {
                    if let header = page.header {
                        HStack {
                            Rectangle()
                                .fill(Color.secondary.opacity(0.2))
                                .frame(height: 1)
                            Text(header)
                                .font(.caption.bold())
                                .foregroundStyle(.secondary)
                                .fixedSize()
                            Rectangle()
                                .fill(Color.secondary.opacity(0.2))
                                .frame(height: 1)
                        }
                    }

                    if page.isScanned {
                        HStack {
                            Image(systemName: "doc.viewfinder")
                                .foregroundStyle(.orange)
                            Text("Scanned page — will be analyzed via Claude Vision")
                                .font(.caption)
                                .foregroundStyle(.orange)
                        }
                        .padding(8)
                        .background(.orange.opacity(0.08))
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                    } else {
                        Text(page.content)
                            .font(.system(.body, design: .monospaced))
                            .textSelection(.enabled)
                    }
                }
                .padding()
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(.secondary.opacity(0.03))
                )
            }
        }
    }

    private var spreadsheetPreview: some View {
        VStack(alignment: .leading, spacing: 16) {
            ForEach(extractedSheets, id: \.self) { sheet in
                VStack(alignment: .leading, spacing: 8) {
                    if let name = sheet.name {
                        Text(name)
                            .font(.headline)
                            .foregroundStyle(.blue)
                    }

                    // Render as table
                    ScrollView(.horizontal) {
                        VStack(alignment: .leading, spacing: 1) {
                            ForEach(Array(sheet.rows.enumerated()), id: \.offset) { rowIdx, row in
                                HStack(spacing: 1) {
                                    ForEach(Array(row.enumerated()), id: \.offset) { _, cell in
                                        Text(cell)
                                            .font(.system(.caption, design: .monospaced))
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .frame(minWidth: 80, alignment: .leading)
                                            .background(rowIdx == 0 ? Color.blue.opacity(0.1) : Color.secondary.opacity(0.03))
                                    }
                                }
                            }
                        }
                    }
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.secondary.opacity(0.15), lineWidth: 1)
                    )
                }
            }
        }
    }

    private var imagePreview: some View {
        VStack(spacing: 12) {
            Image(systemName: "photo.fill")
                .font(.system(size: 64))
                .foregroundStyle(.secondary)
            Text("Image document")
                .font(.headline)
            Text("This image will be analyzed by Claude Vision when reviewed.")
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(40)
    }

    private var textPreview: some View {
        Text(document.extractedText)
            .font(.system(.body, design: .monospaced))
            .textSelection(.enabled)
    }

    // MARK: - Review Panel

    private var reviewPanel: some View {
        VStack(spacing: 0) {
            // Panel header
            HStack {
                Text("Review")
                    .font(.headline)
                Spacer()
                if let r = review {
                    statusBadge(r.status)
                }
            }
            .padding()
            .background(.bar)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    if let r = review {
                        // Show review results
                        reviewResults(r)
                    } else {
                        // Show review form
                        reviewForm
                    }
                }
                .padding()
            }
        }
    }

    private var reviewForm: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Review Focus Areas")
                .font(.subheadline.bold())

            VStack(alignment: .leading, spacing: 6) {
                ForEach(focusOptions, id: \.self) { option in
                    Toggle(option, isOn: Binding(
                        get: { reviewFocus.contains(option) },
                        set: { isOn in
                            if isOn { reviewFocus.append(option) }
                            else { reviewFocus.removeAll { $0 == option } }
                        }
                    ))
                    .font(.callout)
                }
            }

            Text("Custom Instructions")
                .font(.subheadline.bold())

            TextEditor(text: $customInstructions)
                .font(.callout)
                .frame(height: 80)
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.secondary.opacity(0.2), lineWidth: 1)
                )

            Button(action: startReview) {
                if isReviewing {
                    HStack(spacing: 8) {
                        ProgressView()
                            .controlSize(.small)
                        Text("Reviewing with Claude...")
                    }
                } else {
                    Label("Start Review", systemImage: "checkmark.shield")
                }
            }
            .buttonStyle(.borderedProminent)
            .frame(maxWidth: .infinity)
            .disabled(isReviewing)
        }
    }

    private func reviewResults(_ review: ReviewResult) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            // Quick stats
            HStack(spacing: 12) {
                miniStat("\(review.issues.count)", "Issues", .orange)
                miniStat("\(review.highSeverityCount)", "High", .red)
                miniStat("\(review.keyFindings.count)", "Findings", .blue)
            }

            if !review.summary.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Summary")
                        .font(.subheadline.bold())
                    Text(review.summary)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
            }

            if !review.issues.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Issues")
                        .font(.subheadline.bold())
                    ForEach(review.issues) { issue in
                        compactIssue(issue)
                    }
                }
            }

            if !review.keyFindings.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Key Findings")
                        .font(.subheadline.bold())
                    ForEach(review.keyFindings, id: \.self) { finding in
                        HStack(alignment: .top, spacing: 6) {
                            Image(systemName: "arrow.right.circle.fill")
                                .foregroundStyle(.blue)
                                .font(.caption)
                                .padding(.top, 2)
                            Text(finding)
                                .font(.callout)
                        }
                    }
                }
            }
        }
    }

    private func compactIssue(_ issue: ReviewIssue) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Circle()
                    .fill(severityColor(issue.severity))
                    .frame(width: 8, height: 8)
                Text(issue.title)
                    .font(.callout.bold())
                    .strikethrough(issue.resolved)
                Spacer()
                if issue.resolved {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                        .font(.caption)
                }
            }
            Text(issue.description)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(8)
        .background(severityColor(issue.severity).opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 6))
        .opacity(issue.resolved ? 0.5 : 1)
    }

    private func miniStat(_ value: String, _ label: String, _ color: Color) -> some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.title3.bold())
                .foregroundStyle(color)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(8)
        .background(color.opacity(0.06))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func statusBadge(_ status: ReviewStatus) -> some View {
        Text(status.rawValue.capitalized)
            .font(.caption2.bold())
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(statusColor(status).opacity(0.15))
            .foregroundStyle(statusColor(status))
            .clipShape(Capsule())
    }

    private func statusColor(_ status: ReviewStatus) -> Color {
        switch status {
        case .completed: return .green
        case .inProgress: return .orange
        case .failed: return .red
        case .pending: return .gray
        }
    }

    private func severityColor(_ severity: IssueSeverity) -> Color {
        switch severity {
        case .high: return .red
        case .medium: return .orange
        case .low: return .yellow
        case .info: return .blue
        }
    }

    // MARK: - Actions

    private func startReview() {
        Task {
            isReviewing = true
            defer { isReviewing = false }
            do {
                let request = ReviewRequest(
                    documentId: document.id,
                    reviewFocus: reviewFocus,
                    customInstructions: customInstructions
                )
                let result = try await api.reviewDocument(
                    baseURL: appState.serverURL, request: request
                )
                appState.reviews.append(result)
            } catch {
                appState.errorMessage = "Review failed: \(error.localizedDescription)"
            }
        }
    }

    // MARK: - Parsing Helpers

    private var extractedPages: [PageContent] {
        let sections = document.extractedText.components(separatedBy: "--- Page ")
        return sections.compactMap { section in
            guard !section.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return nil }
            let isScanned = section.contains("(scanned)")
            let lines = section.components(separatedBy: "\n")
            let header = lines.first.map { "Page \($0.prefix(while: { $0.isNumber || $0 == " " || $0 == "-" }))" }
            let content = lines.dropFirst().joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines)
            return PageContent(header: header, content: content, isScanned: isScanned)
        }
    }

    private var extractedSheets: [SheetContent] {
        let sections = document.extractedText.components(separatedBy: "=== Sheet: ")
        return sections.compactMap { section in
            guard !section.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return nil }
            let lines = section.components(separatedBy: "\n")
            let name = lines.first?.replacingOccurrences(of: " ===", with: "")
            let rows = lines.dropFirst()
                .filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
                .map { $0.components(separatedBy: "\t") }
            return SheetContent(name: name, rows: rows)
        }
    }

    private var focusOptions: [String] {
        [
            "Mathematical accuracy",
            "Compliance with tax law",
            "Missing schedules or forms",
            "Audit risk areas",
            "Related party transactions",
            "Carryforward items",
            "State tax issues",
        ]
    }

    private var iconForType: String {
        switch document.fileType {
        case "pdf": return "doc.fill"
        case "excel": return "tablecells.fill"
        case "csv": return "tablecells"
        case "image": return "photo.fill"
        default: return "doc"
        }
    }

    private var colorForType: Color {
        switch document.documentType {
        case .taxReturn: return .blue
        case .workPaper: return .green
        case .schedule: return .purple
        case .supportingDoc: return .orange
        case .other: return .gray
        }
    }
}

// MARK: - Helper Types

struct PageContent: Hashable {
    let header: String?
    let content: String
    let isScanned: Bool
}

struct SheetContent: Hashable {
    let name: String?
    let rows: [[String]]
}
