import SwiftUI

struct DocumentDetailView: View {
    let document: TaxDocument
    @EnvironmentObject var appState: AppState
    @State private var showReviewSheet = false
    @State private var isReviewing = false
    @Environment(\.dismiss) private var dismiss
    private let api = APIService()

    private var review: ReviewResult? {
        appState.reviewForDocument(document.id)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                documentHeader
                actionButtons

                if let review = review {
                    reviewSummarySection(review)
                    issuesSection(review)
                    keyFindingsSection(review)
                }

                documentContentPreview
            }
            .padding()
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle(document.filename)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Done") { dismiss() }
            }
        }
        .sheet(isPresented: $showReviewSheet) {
            ReviewOptionsSheet(document: document)
                .environmentObject(appState)
        }
    }

    // MARK: - Header

    private var documentHeader: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(document.documentType.color.opacity(0.12))
                    .frame(width: 64, height: 64)
                Image(systemName: document.documentType.icon)
                    .font(.system(size: 28))
                    .foregroundStyle(document.documentType.color)
            }

            Text(document.documentType.displayName)
                .font(.subheadline.bold())
                .foregroundStyle(document.documentType.color)

            HStack(spacing: 16) {
                Label(document.fileSizeFormatted, systemImage: "doc")
                if let pages = document.pageCount {
                    Label("\(pages) pages", systemImage: "book.pages")
                }
                Label(document.fileType.uppercased(), systemImage: "tag")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Actions

    private var actionButtons: some View {
        HStack(spacing: 12) {
            if review == nil {
                Button {
                    quickReview()
                } label: {
                    HStack {
                        if isReviewing {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Image(systemName: "sparkles")
                        }
                        Text(isReviewing ? "Reviewing..." : "Quick Review")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(isReviewing)

                Button {
                    showReviewSheet = true
                } label: {
                    HStack {
                        Image(systemName: "slider.horizontal.3")
                        Text("Custom")
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            } else {
                Label("Reviewed", systemImage: "checkmark.shield.fill")
                    .font(.headline)
                    .foregroundStyle(.green)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(.green.opacity(0.08), in: RoundedRectangle(cornerRadius: 12))
            }
        }
    }

    // MARK: - Review Summary

    private func reviewSummarySection(_ review: ReviewResult) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Review Summary", systemImage: "doc.text")
                .font(.headline)

            // Tax details
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                taxDetail("Entity", review.entityName)
                taxDetail("Tax Year", review.taxYear)
                taxDetail("Income", review.totalIncome)
                taxDetail("Deductions", review.totalDeductions)
                taxDetail("Tax Liability", review.taxLiability)
                taxDetail("Return Type", review.returnType)
            }

            if !review.summary.isEmpty {
                Text(review.summary)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }

    private func taxDetail(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundStyle(.tertiary)
            Text(value.isEmpty ? "—" : value)
                .font(.subheadline.bold())
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Issues

    private func issuesSection(_ review: ReviewResult) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Label("Issues (\(review.issues.count))", systemImage: "exclamationmark.triangle")
                    .font(.headline)
                Spacer()
                if review.highSeverityCount > 0 {
                    Text("\(review.highSeverityCount) high")
                        .font(.caption.bold())
                        .foregroundStyle(.red)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(.red.opacity(0.1), in: Capsule())
                }
            }

            ForEach(review.issues) { issue in
                IssueRow(issue: issue) {
                    resolveIssue(reviewId: review.id, issue: issue)
                }
            }
        }
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Key Findings

    @ViewBuilder
    private func keyFindingsSection(_ review: ReviewResult) -> some View {
        if !review.keyFindings.isEmpty {
            VStack(alignment: .leading, spacing: 10) {
                Label("Key Findings", systemImage: "lightbulb.fill")
                    .font(.headline)

                ForEach(review.keyFindings, id: \.self) { finding in
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "arrow.right.circle.fill")
                            .foregroundStyle(.blue)
                            .font(.caption)
                            .padding(.top, 2)
                        Text(finding)
                            .font(.subheadline)
                    }
                }
            }
            .padding()
            .background(.background, in: RoundedRectangle(cornerRadius: 16))
        }
    }

    // MARK: - Content Preview

    private var documentContentPreview: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Content Preview", systemImage: "text.alignleft")
                .font(.headline)

            Text(cleanText(String(document.extractedText.prefix(2000))))
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.secondary)
                .textSelection(.enabled)

            if document.extractedText.count > 2000 {
                Text("... and more")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                    .italic()
            }
        }
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }

    // MARK: - Actions

    private func quickReview() {
        Task {
            isReviewing = true
            defer { isReviewing = false }
            do {
                let request = ReviewRequest(documentId: document.id, reviewFocus: [], customInstructions: "")
                let result = try await api.reviewDocument(baseURL: appState.serverURL, request: request)
                appState.reviews.append(result)
            } catch {
                appState.showError("Review failed: \(error.localizedDescription)")
            }
        }
    }

    private func resolveIssue(reviewId: String, issue: ReviewIssue) {
        Task {
            do {
                _ = try await api.resolveIssue(baseURL: appState.serverURL, reviewId: reviewId, issueId: issue.id)
                if let idx = appState.reviews.firstIndex(where: { $0.id == reviewId }),
                   let iIdx = appState.reviews[idx].issues.firstIndex(where: { $0.id == issue.id }) {
                    withAnimation { appState.reviews[idx].issues[iIdx].resolved = true }
                }
            } catch {
                appState.showError("Failed to resolve: \(error.localizedDescription)")
            }
        }
    }

    private func cleanText(_ text: String) -> String {
        text.replacingOccurrences(
            of: "\\[IMAGE:data:image/[^\\]]+\\]",
            with: "[scanned page]",
            options: .regularExpression
        )
    }
}

// MARK: - Issue Row

struct IssueRow: View {
    let issue: ReviewIssue
    let onResolve: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: issue.severity.icon)
                    .foregroundStyle(issue.severity.color)
                    .font(.subheadline)

                Text(issue.title)
                    .font(.subheadline.bold())
                    .strikethrough(issue.resolved)
                    .lineLimit(2)

                Spacer()

                if issue.resolved {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                } else {
                    Button("Resolve", action: onResolve)
                        .font(.caption)
                        .buttonStyle(.bordered)
                        .controlSize(.mini)
                }
            }

            Text(issue.description)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(3)

            if !issue.recommendation.isEmpty {
                HStack(alignment: .top, spacing: 4) {
                    Image(systemName: "lightbulb.fill")
                        .foregroundStyle(.yellow)
                        .font(.caption2)
                    Text(issue.recommendation)
                        .font(.caption)
                        .italic()
                }
                .padding(8)
                .background(.yellow.opacity(0.06), in: RoundedRectangle(cornerRadius: 6))
            }
        }
        .padding(12)
        .background(issue.severity.color.opacity(issue.resolved ? 0.02 : 0.05), in: RoundedRectangle(cornerRadius: 10))
        .opacity(issue.resolved ? 0.6 : 1)
    }
}

// MARK: - Review Options Sheet

struct ReviewOptionsSheet: View {
    let document: TaxDocument
    @EnvironmentObject var appState: AppState
    @State private var selectedFocusAreas: Set<String> = []
    @State private var customInstructions = ""
    @State private var isReviewing = false
    @Environment(\.dismiss) private var dismiss
    private let api = APIService()

    private let focusOptions = [
        "Mathematical accuracy",
        "Compliance with tax law",
        "Missing schedules or forms",
        "Audit risk areas",
        "Related party transactions",
        "Carryforward items",
        "State tax issues",
    ]

    var body: some View {
        NavigationStack {
            List {
                Section("Focus Areas") {
                    ForEach(focusOptions, id: \.self) { option in
                        Button {
                            if selectedFocusAreas.contains(option) {
                                selectedFocusAreas.remove(option)
                            } else {
                                selectedFocusAreas.insert(option)
                            }
                        } label: {
                            HStack {
                                Text(option)
                                    .foregroundStyle(.primary)
                                Spacer()
                                if selectedFocusAreas.contains(option) {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(.blue)
                                }
                            }
                        }
                    }
                }

                Section("Custom Instructions") {
                    TextEditor(text: $customInstructions)
                        .frame(minHeight: 80)
                }
            }
            .navigationTitle("Review Options")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        startReview()
                    } label: {
                        if isReviewing {
                            ProgressView()
                        } else {
                            Text("Start Review")
                        }
                    }
                    .disabled(isReviewing)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    private func startReview() {
        Task {
            isReviewing = true
            defer { isReviewing = false }
            do {
                let request = ReviewRequest(
                    documentId: document.id,
                    reviewFocus: Array(selectedFocusAreas),
                    customInstructions: customInstructions
                )
                let result = try await api.reviewDocument(baseURL: appState.serverURL, request: request)
                appState.reviews.append(result)
                dismiss()
            } catch {
                appState.showError("Review failed: \(error.localizedDescription)")
            }
        }
    }
}
