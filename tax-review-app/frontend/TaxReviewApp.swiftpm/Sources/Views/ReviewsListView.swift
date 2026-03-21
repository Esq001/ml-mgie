import SwiftUI

struct ReviewsListView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        HSplitView {
            // Review list
            reviewList
                .frame(minWidth: 300, maxWidth: 400)

            // Detail panel
            if let review = appState.selectedReview {
                ReviewDetailView(review: review)
            } else {
                noSelectionView
            }
        }
    }

    private var reviewList: some View {
        VStack(spacing: 0) {
            // Summary bar
            HStack {
                Label("\(appState.reviews.count) Reviews", systemImage: "checkmark.shield")
                Spacer()
                if appState.highPriorityIssues > 0 {
                    Label("\(appState.highPriorityIssues) High", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.red)
                        .font(.caption)
                }
            }
            .padding()
            .background(.bar)

            Divider()

            List(appState.reviews, selection: $appState.selectedReviewId) { review in
                ReviewRow(review: review, documentName: documentName(for: review))
                    .tag(review.id)
            }
        }
    }

    private var noSelectionView: some View {
        VStack(spacing: 16) {
            Image(systemName: "checkmark.shield")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("Select a review to see details")
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func documentName(for review: ReviewResult) -> String {
        appState.documents.first { $0.id == review.documentId }?.filename ?? "Unknown"
    }
}

struct ReviewRow: View {
    let review: ReviewResult
    let documentName: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(review.entityName.isEmpty ? documentName : review.entityName)
                    .font(.headline)
                Spacer()
                statusBadge
            }

            if !review.taxYear.isEmpty {
                Text("Tax Year: \(review.taxYear)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 12) {
                issueCount(review.issues.filter { $0.severity == .high && !$0.resolved }.count, "High", .red)
                issueCount(review.issues.filter { $0.severity == .medium && !$0.resolved }.count, "Med", .orange)
                issueCount(review.issues.filter { $0.severity == .low && !$0.resolved }.count, "Low", .yellow)
            }
        }
        .padding(.vertical, 4)
    }

    private var statusBadge: some View {
        Text(review.status.rawValue.capitalized)
            .font(.caption2)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(statusColor.opacity(0.15))
            .foregroundStyle(statusColor)
            .clipShape(Capsule())
    }

    private var statusColor: Color {
        switch review.status {
        case .completed: return .green
        case .inProgress: return .orange
        case .failed: return .red
        case .pending: return .gray
        }
    }

    @ViewBuilder
    private func issueCount(_ count: Int, _ label: String, _ color: Color) -> some View {
        if count > 0 {
            HStack(spacing: 2) {
                Circle().fill(color).frame(width: 6, height: 6)
                Text("\(count) \(label)")
                    .font(.caption2)
            }
        }
    }
}
