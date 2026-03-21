import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Hero stats row
                statsRow

                // Two-column layout
                HStack(alignment: .top, spacing: 20) {
                    // Left column
                    VStack(spacing: 20) {
                        issuesBySeverityChart
                        recentActivity
                    }

                    // Right column
                    VStack(spacing: 20) {
                        documentsByTypeChart
                        reviewProgress
                    }
                }
            }
            .padding(24)
        }
        .background(Color(nsColor: .windowBackgroundColor))
    }

    // MARK: - Stats Row

    private var statsRow: some View {
        HStack(spacing: 16) {
            StatCard(
                title: "Documents",
                value: "\(appState.documents.count)",
                icon: "doc.on.doc.fill",
                color: .blue,
                subtitle: pluralize(appState.documents.count, "file")
            )
            StatCard(
                title: "Reviews",
                value: "\(appState.reviews.count)",
                icon: "checkmark.shield.fill",
                color: .green,
                subtitle: "\(completedReviews) completed"
            )
            StatCard(
                title: "Open Issues",
                value: "\(appState.totalIssues)",
                icon: "exclamationmark.triangle.fill",
                color: appState.highPriorityIssues > 0 ? .red : .orange,
                subtitle: "\(appState.highPriorityIssues) high priority"
            )
            StatCard(
                title: "Resolved",
                value: "\(resolvedIssues)",
                icon: "checkmark.circle.fill",
                color: .mint,
                subtitle: resolvedPercentage
            )
        }
    }

    // MARK: - Issues by Severity Chart

    private var issuesBySeverityChart: some View {
        DashboardCard(title: "Issues by Severity", icon: "chart.bar.fill") {
            if allIssues.isEmpty {
                emptyChartPlaceholder("No issues found yet")
            } else {
                VStack(spacing: 12) {
                    severityBar("High", count: highCount, total: allIssues.count, color: .red)
                    severityBar("Medium", count: mediumCount, total: allIssues.count, color: .orange)
                    severityBar("Low", count: lowCount, total: allIssues.count, color: .yellow)
                    severityBar("Info", count: infoCount, total: allIssues.count, color: .blue)
                }
            }
        }
    }

    private func severityBar(_ label: String, count: Int, total: Int, color: Color) -> some View {
        HStack(spacing: 12) {
            Text(label)
                .font(.caption)
                .frame(width: 50, alignment: .trailing)
                .foregroundStyle(.secondary)

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(color.opacity(0.1))

                    RoundedRectangle(cornerRadius: 4)
                        .fill(color.gradient)
                        .frame(width: total > 0 ? max(4, geo.size.width * CGFloat(count) / CGFloat(total)) : 0)
                }
            }
            .frame(height: 24)

            Text("\(count)")
                .font(.caption.bold())
                .frame(width: 30, alignment: .leading)
        }
    }

    // MARK: - Documents by Type Chart

    private var documentsByTypeChart: some View {
        DashboardCard(title: "Documents by Type", icon: "doc.circle.fill") {
            if appState.documents.isEmpty {
                emptyChartPlaceholder("No documents uploaded")
            } else {
                VStack(spacing: 8) {
                    ForEach(documentTypeCounts, id: \.type) { item in
                        HStack(spacing: 12) {
                            Circle()
                                .fill(item.color)
                                .frame(width: 10, height: 10)
                            Text(item.type.displayName)
                                .font(.callout)
                            Spacer()
                            Text("\(item.count)")
                                .font(.callout.bold())
                                .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 2)
                    }
                }
            }
        }
    }

    // MARK: - Review Progress

    private var reviewProgress: some View {
        DashboardCard(title: "Review Progress", icon: "gauge.medium") {
            if appState.reviews.isEmpty {
                emptyChartPlaceholder("No reviews started")
            } else {
                VStack(spacing: 16) {
                    // Progress ring
                    ZStack {
                        Circle()
                            .stroke(Color.secondary.opacity(0.1), lineWidth: 12)
                        Circle()
                            .trim(from: 0, to: completionFraction)
                            .stroke(Color.green.gradient, style: StrokeStyle(lineWidth: 12, lineCap: .round))
                            .rotationEffect(.degrees(-90))
                            .animation(.easeInOut(duration: 0.8), value: completionFraction)

                        VStack(spacing: 2) {
                            Text("\(Int(completionFraction * 100))%")
                                .font(.title2.bold())
                            Text("Complete")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .frame(width: 100, height: 100)

                    HStack(spacing: 20) {
                        progressStat("Pending", count: pendingReviews, color: .gray)
                        progressStat("In Progress", count: inProgressReviews, color: .orange)
                        progressStat("Completed", count: completedReviews, color: .green)
                        progressStat("Failed", count: failedReviews, color: .red)
                    }
                }
            }
        }
    }

    private func progressStat(_ label: String, count: Int, color: Color) -> some View {
        VStack(spacing: 4) {
            Text("\(count)")
                .font(.headline)
                .foregroundStyle(color)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Recent Activity

    private var recentActivity: some View {
        DashboardCard(title: "Recent Activity", icon: "clock.fill") {
            if appState.reviews.isEmpty && appState.documents.isEmpty {
                emptyChartPlaceholder("No activity yet")
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(appState.reviews.prefix(5).enumerated()), id: \.element.id) { index, review in
                        HStack(spacing: 12) {
                            Image(systemName: statusIcon(review.status))
                                .foregroundStyle(statusColor(review.status))
                                .frame(width: 20)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(review.entityName.isEmpty ? "Review" : review.entityName)
                                    .font(.callout)
                                Text("\(review.issues.count) issues found")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }

                            Spacer()

                            if review.highSeverityCount > 0 {
                                HStack(spacing: 2) {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .font(.caption2)
                                    Text("\(review.highSeverityCount)")
                                        .font(.caption2.bold())
                                }
                                .foregroundStyle(.red)
                            }
                        }
                        .padding(.vertical, 8)

                        if index < min(appState.reviews.count, 5) - 1 {
                            Divider()
                        }
                    }
                }
            }
        }
    }

    // MARK: - Helpers

    private func emptyChartPlaceholder(_ message: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: "chart.bar")
                .font(.title)
                .foregroundStyle(.quaternary)
            Text(message)
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 80)
    }

    private func statusIcon(_ status: ReviewStatus) -> String {
        switch status {
        case .completed: return "checkmark.circle.fill"
        case .inProgress: return "arrow.triangle.2.circlepath"
        case .failed: return "xmark.circle.fill"
        case .pending: return "clock"
        }
    }

    private func statusColor(_ status: ReviewStatus) -> Color {
        switch status {
        case .completed: return .green
        case .inProgress: return .orange
        case .failed: return .red
        case .pending: return .gray
        }
    }

    private func pluralize(_ count: Int, _ word: String) -> String {
        count == 1 ? "1 \(word)" : "\(count) \(word)s"
    }

    // MARK: - Computed Properties

    private var allIssues: [ReviewIssue] {
        appState.reviews.flatMap(\.issues)
    }

    private var highCount: Int { allIssues.filter { $0.severity == .high }.count }
    private var mediumCount: Int { allIssues.filter { $0.severity == .medium }.count }
    private var lowCount: Int { allIssues.filter { $0.severity == .low }.count }
    private var infoCount: Int { allIssues.filter { $0.severity == .info }.count }

    private var resolvedIssues: Int { allIssues.filter(\.resolved).count }
    private var resolvedPercentage: String {
        guard !allIssues.isEmpty else { return "—" }
        let pct = Int(Double(resolvedIssues) / Double(allIssues.count) * 100)
        return "\(pct)% of all issues"
    }

    private var completedReviews: Int {
        appState.reviews.filter { $0.status == .completed }.count
    }
    private var pendingReviews: Int {
        appState.reviews.filter { $0.status == .pending }.count
    }
    private var inProgressReviews: Int {
        appState.reviews.filter { $0.status == .inProgress }.count
    }
    private var failedReviews: Int {
        appState.reviews.filter { $0.status == .failed }.count
    }

    private var completionFraction: CGFloat {
        guard !appState.reviews.isEmpty else { return 0 }
        return CGFloat(completedReviews) / CGFloat(appState.reviews.count)
    }

    private var documentTypeCounts: [(type: DocumentType, count: Int, color: Color)] {
        let grouped = Dictionary(grouping: appState.documents, by: \.documentType)
        let colors: [DocumentType: Color] = [
            .taxReturn: .blue,
            .workPaper: .green,
            .schedule: .purple,
            .supportingDoc: .orange,
            .other: .gray,
        ]
        return grouped.map { (type: $0.key, count: $0.value.count, color: colors[$0.key] ?? .gray) }
            .sorted { $0.count > $1.count }
    }
}

// MARK: - Stat Card

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    let subtitle: String

    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundStyle(color)
                Spacer()
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(value)
                    .font(.system(size: 32, weight: .bold, design: .rounded))

                Text(title)
                    .font(.subheadline.bold())
                    .foregroundStyle(.secondary)

                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(.background)
                .shadow(color: .black.opacity(isHovered ? 0.08 : 0.04), radius: isHovered ? 12 : 6, y: isHovered ? 4 : 2)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(color.opacity(isHovered ? 0.3 : 0.1), lineWidth: 1)
        )
        .scaleEffect(isHovered ? 1.02 : 1.0)
        .animation(.easeInOut(duration: 0.2), value: isHovered)
        .onHover { isHovered = $0 }
    }
}

// MARK: - Dashboard Card

struct DashboardCard<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .foregroundStyle(.secondary)
                Text(title)
                    .font(.headline)
            }

            content()
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(.background)
                .shadow(color: .black.opacity(0.04), radius: 6, y: 2)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.secondary.opacity(0.1), lineWidth: 1)
        )
    }
}
