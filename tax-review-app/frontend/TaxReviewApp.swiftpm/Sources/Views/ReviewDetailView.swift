import SwiftUI

struct ReviewDetailView: View {
    let review: ReviewResult
    @EnvironmentObject var appState: AppState
    @State private var selectedFilter: IssueSeverity?
    @State private var showRawAnalysis = false
    private let api = APIService()

    var filteredIssues: [ReviewIssue] {
        if let filter = selectedFilter {
            return review.issues.filter { $0.severity == filter }
        }
        return review.issues
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                headerSection
                summaryCard
                keyFindingsSection
                issuesSection
            }
            .padding()
        }
        .sheet(isPresented: $showRawAnalysis) {
            rawAnalysisSheet
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading) {
                    Text(review.entityName.isEmpty ? "Tax Review" : review.entityName)
                        .font(.title)
                    if !review.returnType.isEmpty {
                        Text(review.returnType)
                            .font(.title3)
                            .foregroundStyle(.secondary)
                    }
                }
                Spacer()
                Button("View Raw Analysis") { showRawAnalysis = true }
                    .buttonStyle(.bordered)
            }

            // Tax details grid
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 12) {
                detailCard("Tax Year", review.taxYear)
                detailCard("Total Income", review.totalIncome)
                detailCard("Deductions", review.totalDeductions)
                detailCard("Tax Liability", review.taxLiability)
            }
        }
    }

    private func detailCard(_ label: String, _ value: String) -> some View {
        VStack(spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value.isEmpty ? "—" : value)
                .font(.headline)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(.secondary.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    // MARK: - Summary

    private var summaryCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Summary")
                .font(.title3.bold())
            Text(review.summary)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.secondary.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Key Findings

    @ViewBuilder
    private var keyFindingsSection: some View {
        if !review.keyFindings.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                Text("Key Findings")
                    .font(.title3.bold())
                ForEach(review.keyFindings, id: \.self) { finding in
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "arrow.right.circle.fill")
                            .foregroundStyle(.blue)
                            .font(.caption)
                            .padding(.top, 2)
                        Text(finding)
                            .font(.body)
                    }
                }
            }
        }
    }

    // MARK: - Issues

    private var issuesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Issues (\(review.issues.count))")
                    .font(.title3.bold())
                Spacer()
                Picker("Filter", selection: $selectedFilter) {
                    Text("All").tag(nil as IssueSeverity?)
                    ForEach(IssueSeverity.allCases, id: \.self) { severity in
                        Text(severity.rawValue.capitalized).tag(severity as IssueSeverity?)
                    }
                }
                .pickerStyle(.segmented)
                .frame(width: 300)
            }

            ForEach(filteredIssues) { issue in
                IssueCard(issue: issue) {
                    resolveIssue(issue)
                }
            }
        }
    }

    // MARK: - Raw Analysis Sheet

    private var rawAnalysisSheet: some View {
        VStack {
            HStack {
                Text("Raw Analysis")
                    .font(.title2.bold())
                Spacer()
                Button("Done") { showRawAnalysis = false }
                    .buttonStyle(.borderedProminent)
            }
            .padding()

            ScrollView {
                Text(review.rawAnalysis)
                    .font(.system(.body, design: .monospaced))
                    .textSelection(.enabled)
                    .padding()
            }
        }
        .frame(minWidth: 700, minHeight: 500)
    }

    // MARK: - Actions

    private func resolveIssue(_ issue: ReviewIssue) {
        Task {
            do {
                _ = try await api.resolveIssue(
                    baseURL: appState.serverURL,
                    reviewId: review.id,
                    issueId: issue.id
                )
                if let idx = appState.reviews.firstIndex(where: { $0.id == review.id }),
                   let issueIdx = appState.reviews[idx].issues.firstIndex(where: { $0.id == issue.id }) {
                    appState.reviews[idx].issues[issueIdx].resolved = true
                }
            } catch {
                appState.errorMessage = "Failed to resolve issue: \(error.localizedDescription)"
            }
        }
    }
}

// MARK: - Issue Card

struct IssueCard: View {
    let issue: ReviewIssue
    let onResolve: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                severityBadge
                Text(issue.category)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                if !issue.resolved {
                    Button("Resolve") { onResolve() }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                } else {
                    Label("Resolved", systemImage: "checkmark.circle.fill")
                        .font(.caption)
                        .foregroundStyle(.green)
                }
            }

            Text(issue.title)
                .font(.headline)
                .strikethrough(issue.resolved)

            Text(issue.description)
                .font(.body)
                .foregroundStyle(.secondary)

            if !issue.location.isEmpty {
                Label(issue.location, systemImage: "mappin")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }

            if !issue.recommendation.isEmpty {
                HStack(alignment: .top, spacing: 4) {
                    Image(systemName: "lightbulb.fill")
                        .foregroundStyle(.yellow)
                        .font(.caption)
                    Text(issue.recommendation)
                        .font(.callout)
                        .italic()
                }
                .padding(8)
                .background(.yellow.opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: 6))
            }
        }
        .padding()
        .background(.secondary.opacity(issue.resolved ? 0.02 : 0.05))
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .opacity(issue.resolved ? 0.6 : 1)
    }

    private var severityBadge: some View {
        Text(issue.severity.rawValue.uppercased())
            .font(.caption2.bold())
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(severityColor.opacity(0.15))
            .foregroundStyle(severityColor)
            .clipShape(Capsule())
    }

    private var severityColor: Color {
        switch issue.severity {
        case .high: return .red
        case .medium: return .orange
        case .low: return .yellow
        case .info: return .blue
        }
    }
}
