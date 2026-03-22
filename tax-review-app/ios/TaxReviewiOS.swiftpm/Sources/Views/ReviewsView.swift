import SwiftUI

struct ReviewsView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedReview: ReviewResult?
    @State private var filterSeverity: IssueSeverity?

    var body: some View {
        NavigationStack {
            Group {
                if appState.reviews.isEmpty {
                    emptyState
                } else {
                    reviewList
                }
            }
            .navigationTitle("Reviews")
            .sheet(item: $selectedReview) { review in
                NavigationStack {
                    ReviewFullDetailView(review: review)
                        .environmentObject(appState)
                }
            }
        }
    }

    private var emptyState: some View {
        ContentUnavailableView {
            Label("No Reviews", systemImage: "checkmark.shield")
        } description: {
            Text("Review documents from the Documents tab to see results here")
        }
    }

    private var reviewList: some View {
        List {
            // Summary section
            Section {
                HStack(spacing: 16) {
                    miniStat("\(appState.reviews.count)", "Total", .blue)
                    miniStat("\(appState.totalIssues)", "Issues", .orange)
                    miniStat("\(appState.highPriorityIssues)", "High", .red)
                    miniStat("\(appState.resolvedIssues)", "Fixed", .green)
                }
                .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
            }

            // Severity filter
            Section {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        filterChip("All", isSelected: filterSeverity == nil) {
                            filterSeverity = nil
                        }
                        ForEach(IssueSeverity.allCases, id: \.self) { severity in
                            filterChip(severity.rawValue.capitalized, color: severity.color, isSelected: filterSeverity == severity) {
                                filterSeverity = severity
                            }
                        }
                    }
                }
                .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
            }

            // Reviews
            Section("Reviews") {
                ForEach(filteredReviews) { review in
                    Button {
                        selectedReview = review
                    } label: {
                        ReviewListRow(
                            review: review,
                            documentName: appState.documents.first { $0.id == review.documentId }?.filename ?? "Unknown"
                        )
                    }
                }
            }
        }
        .listStyle(.insetGrouped)
    }

    private var filteredReviews: [ReviewResult] {
        guard let severity = filterSeverity else { return appState.reviews }
        return appState.reviews.filter { review in
            review.issues.contains { $0.severity == severity && !$0.resolved }
        }
    }

    private func miniStat(_ value: String, _ label: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.title3.bold().monospacedDigit())
                .foregroundStyle(color)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private func filterChip(_ label: String, color: Color = .blue, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.caption.bold())
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? color.opacity(0.15) : Color.secondary.opacity(0.08), in: Capsule())
                .foregroundStyle(isSelected ? color : .secondary)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Review List Row

struct ReviewListRow: View {
    let review: ReviewResult
    let documentName: String

    var body: some View {
        HStack(spacing: 12) {
            // Status icon
            ZStack {
                Circle()
                    .fill(review.status.color.opacity(0.12))
                    .frame(width: 40, height: 40)
                Image(systemName: review.status.icon)
                    .foregroundStyle(review.status.color)
            }

            VStack(alignment: .leading, spacing: 3) {
                Text(review.entityName.isEmpty ? documentName : review.entityName)
                    .font(.body)
                    .foregroundStyle(.primary)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    if !review.taxYear.isEmpty {
                        Text(review.taxYear)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                    if !review.returnType.isEmpty {
                        Text(review.returnType)
                            .font(.caption2)
                            .padding(.horizontal, 5)
                            .padding(.vertical, 1)
                            .background(.secondary.opacity(0.1), in: Capsule())
                            .foregroundStyle(.secondary)
                    }
                }

                // Issue severity pills
                HStack(spacing: 4) {
                    let high = review.issues.filter { $0.severity == .high && !$0.resolved }.count
                    let med = review.issues.filter { $0.severity == .medium && !$0.resolved }.count
                    let low = review.issues.filter { $0.severity == .low && !$0.resolved }.count

                    if high > 0 { severityPill("\(high)", .red) }
                    if med > 0 { severityPill("\(med)", .orange) }
                    if low > 0 { severityPill("\(low)", .yellow) }

                    if high == 0 && med == 0 && low == 0 && review.status == .completed {
                        Text("No open issues")
                            .font(.caption2)
                            .foregroundStyle(.green)
                    }
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.caption2)
                .foregroundStyle(.quaternary)
        }
        .padding(.vertical, 4)
    }

    private func severityPill(_ count: String, _ color: Color) -> some View {
        HStack(spacing: 2) {
            Circle().fill(color).frame(width: 5, height: 5)
            Text(count)
                .font(.caption2.bold())
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(color.opacity(0.1), in: Capsule())
        .foregroundStyle(color)
    }
}

// MARK: - Review Full Detail View

struct ReviewFullDetailView: View {
    let review: ReviewResult
    @EnvironmentObject var appState: AppState
    @State private var showRawAnalysis = false
    @Environment(\.dismiss) private var dismiss
    private let api = APIService()

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header stats
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3), spacing: 12) {
                    statBox("\(review.issues.count)", "Issues", .orange)
                    statBox("\(review.highSeverityCount)", "High", .red)
                    statBox("\(review.keyFindings.count)", "Findings", .blue)
                }

                // Tax info
                if !review.entityName.isEmpty || !review.taxYear.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Tax Details", systemImage: "building.columns")
                            .font(.headline)
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                            taxField("Entity", review.entityName)
                            taxField("Year", review.taxYear)
                            taxField("Income", review.totalIncome)
                            taxField("Deductions", review.totalDeductions)
                            taxField("Liability", review.taxLiability)
                            taxField("Type", review.returnType)
                        }
                    }
                    .padding()
                    .background(.background, in: RoundedRectangle(cornerRadius: 16))
                }

                // Summary
                if !review.summary.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Label("Summary", systemImage: "text.alignleft")
                            .font(.headline)
                        Text(review.summary)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(.background, in: RoundedRectangle(cornerRadius: 16))
                }

                // Issues
                if !review.issues.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Label("Issues", systemImage: "exclamationmark.triangle")
                            .font(.headline)
                        ForEach(review.issues) { issue in
                            IssueRow(issue: issue) {
                                resolveIssue(issue)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(.background, in: RoundedRectangle(cornerRadius: 16))
                }

                // Key findings
                if !review.keyFindings.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
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
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(.background, in: RoundedRectangle(cornerRadius: 16))
                }

                // Raw analysis button
                Button {
                    showRawAnalysis = true
                } label: {
                    Label("View Raw Analysis", systemImage: "doc.plaintext")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }
            .padding()
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle(review.entityName.isEmpty ? "Review" : review.entityName)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("Done") { dismiss() }
            }
        }
        .sheet(isPresented: $showRawAnalysis) {
            NavigationStack {
                ScrollView {
                    Text(review.rawAnalysis)
                        .font(.system(.caption, design: .monospaced))
                        .textSelection(.enabled)
                        .padding()
                }
                .navigationTitle("Raw Analysis")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") { showRawAnalysis = false }
                    }
                    ToolbarItem(placement: .primaryAction) {
                        ShareLink(item: review.rawAnalysis)
                    }
                }
            }
        }
    }

    private func statBox(_ value: String, _ label: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.title2.bold().monospacedDigit())
                .foregroundStyle(color)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(color.opacity(0.06), in: RoundedRectangle(cornerRadius: 12))
    }

    private func taxField(_ label: String, _ value: String) -> some View {
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

    private func resolveIssue(_ issue: ReviewIssue) {
        Task {
            do {
                _ = try await api.resolveIssue(baseURL: appState.serverURL, reviewId: review.id, issueId: issue.id)
                if let idx = appState.reviews.firstIndex(where: { $0.id == review.id }),
                   let iIdx = appState.reviews[idx].issues.firstIndex(where: { $0.id == issue.id }) {
                    withAnimation { appState.reviews[idx].issues[iIdx].resolved = true }
                }
            } catch {
                appState.showError("Failed: \(error.localizedDescription)")
            }
        }
    }
}

// MARK: - Make ReviewResult work with sheet

extension ReviewResult: @retroactive Hashable {
    public static func == (lhs: ReviewResult, rhs: ReviewResult) -> Bool { lhs.id == rhs.id }
    public func hash(into hasher: inout Hasher) { hasher.combine(id) }
}
