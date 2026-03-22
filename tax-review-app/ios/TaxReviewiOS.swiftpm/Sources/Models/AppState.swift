import SwiftUI

@MainActor
class AppState: ObservableObject {
    @Published var documents: [TaxDocument] = []
    @Published var reviews: [ReviewResult] = []
    @Published var comparisons: [ComparisonResult] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var serverURL = "http://localhost:8000"

    @AppStorage("serverURL") private var savedServerURL = "http://localhost:8000"

    func reviewForDocument(_ docId: String) -> ReviewResult? {
        reviews.first { $0.documentId == docId }
    }

    var totalIssues: Int {
        reviews.reduce(0) { $0 + $1.unresolvedIssueCount }
    }

    var highPriorityIssues: Int {
        reviews.reduce(0) { $0 + $1.highSeverityCount }
    }

    var completedReviews: Int {
        reviews.filter { $0.status == .completed }.count
    }

    var resolvedIssues: Int {
        reviews.flatMap(\.issues).filter(\.resolved).count
    }

    var allIssues: [ReviewIssue] {
        reviews.flatMap(\.issues)
    }

    init() {
        serverURL = savedServerURL
    }

    func updateServerURL(_ url: String) {
        serverURL = url
        savedServerURL = url
    }

    func showError(_ message: String) {
        errorMessage = message
        Task {
            try? await Task.sleep(for: .seconds(4))
            if errorMessage == message {
                errorMessage = nil
            }
        }
    }
}
