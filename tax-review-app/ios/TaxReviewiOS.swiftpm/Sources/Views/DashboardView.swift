import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    statsGrid
                    issuesSummaryCard
                    recentReviewsCard
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Dashboard")
            .refreshable {
                await refreshData()
            }
        }
    }

    // MARK: - Stats Grid

    private var statsGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            StatCard(
                icon: "doc.on.doc.fill",
                value: "\(appState.documents.count)",
                label: "Documents",
                color: .blue
            )
            StatCard(
                icon: "checkmark.shield.fill",
                value: "\(appState.reviews.count)",
                label: "Reviews",
                color: .green
            )
            StatCard(
                icon: "exclamationmark.triangle.fill",
                value: "\(appState.totalIssues)",
                label: "Open Issues",
                color: appState.highPriorityIssues > 0 ? .red : .orange
            )
            StatCard(
                icon: "checkmark.circle.fill",
                value: "\(appState.resolvedIssues)",
                label: "Resolved",
                color: .mint
            )
        }
    }

    // MARK: - Issues Summary

    private var issuesSummaryCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Issues by Severity", systemImage: "chart.bar.fill")
                .font(.headline)

            if appState.allIssues.isEmpty {
                HStack {
                    Spacer()
                    VStack(spacing: 6) {
                        Image(systemName: "checkmark.seal")
                            .font(.title)
                            .foregroundStyle(.green)
                        Text("No issues found")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical)
                    Spacer()
                }
            } else {
                VStack(spacing: 8) {
                    severityRow("High", count: countBySeverity(.high), color: .red)
                    severityRow("Medium", count: countBySeverity(.medium), color: .orange)
                    severityRow("Low", count: countBySeverity(.low), color: .yellow)
                    severityRow("Info", count: countBySeverity(.info), color: .blue)
                }
            }
        }
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }

    private func severityRow(_ label: String, count: Int, color: Color) -> some View {
        HStack(spacing: 10) {
            Text(label)
                .font(.subheadline)
                .frame(width: 55, alignment: .leading)
                .foregroundStyle(.secondary)

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(color.opacity(0.12))
                    Capsule()
                        .fill(color.gradient)
                        .frame(width: barWidth(count: count, total: appState.allIssues.count, available: geo.size.width))
                }
            }
            .frame(height: 22)

            Text("\(count)")
                .font(.subheadline.bold().monospacedDigit())
                .frame(width: 28, alignment: .trailing)
        }
    }

    private func barWidth(count: Int, total: Int, available: CGFloat) -> CGFloat {
        guard total > 0 else { return 0 }
        return max(4, available * CGFloat(count) / CGFloat(total))
    }

    // MARK: - Recent Reviews

    private var recentReviewsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Recent Reviews", systemImage: "clock.fill")
                .font(.headline)

            if appState.reviews.isEmpty {
                HStack {
                    Spacer()
                    VStack(spacing: 6) {
                        Image(systemName: "doc.text.magnifyingglass")
                            .font(.title)
                            .foregroundStyle(.secondary)
                        Text("No reviews yet")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical)
                    Spacer()
                }
            } else {
                ForEach(Array(appState.reviews.prefix(5).enumerated()), id: \.element.id) { index, review in
                    if index > 0 { Divider() }
                    recentReviewRow(review)
                }
            }
        }
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }

    private func recentReviewRow(_ review: ReviewResult) -> some View {
        HStack(spacing: 12) {
            Image(systemName: review.status.icon)
                .foregroundStyle(review.status.color)
                .font(.title3)

            VStack(alignment: .leading, spacing: 2) {
                Text(review.entityName.isEmpty ? "Review" : review.entityName)
                    .font(.subheadline.bold())
                Text("\(review.issues.count) issues  ·  \(review.status.label)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            if review.highSeverityCount > 0 {
                HStack(spacing: 3) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.caption2)
                    Text("\(review.highSeverityCount)")
                        .font(.caption.bold())
                }
                .foregroundStyle(.red)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(.red.opacity(0.1), in: Capsule())
            }
        }
    }

    // MARK: - Helpers

    private func countBySeverity(_ severity: IssueSeverity) -> Int {
        appState.allIssues.filter { $0.severity == severity }.count
    }

    private func refreshData() async {
        let api = APIService()
        do {
            async let docs = api.fetchDocuments(baseURL: appState.serverURL)
            async let revs = api.fetchReviews(baseURL: appState.serverURL)
            appState.documents = try await docs
            appState.reviews = try await revs
        } catch {
            appState.showError("Refresh failed: \(error.localizedDescription)")
        }
    }
}

// MARK: - Stat Card

struct StatCard: View {
    let icon: String
    let value: String
    let label: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(color)

            Text(value)
                .font(.system(size: 28, weight: .bold, design: .rounded))

            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.background, in: RoundedRectangle(cornerRadius: 16))
    }
}
