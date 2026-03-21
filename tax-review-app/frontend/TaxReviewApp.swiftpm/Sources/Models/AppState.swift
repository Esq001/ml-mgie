import SwiftUI

@MainActor
class AppState: ObservableObject {
    @Published var documents: [TaxDocument] = []
    @Published var reviews: [ReviewResult] = []
    @Published var comparisons: [ComparisonResult] = []
    @Published var selectedDocumentId: String?
    @Published var selectedReviewId: String?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var serverURL = "http://localhost:8000"

    @AppStorage("serverURL") private var savedServerURL = "http://localhost:8000"

    var selectedDocument: TaxDocument? {
        documents.first { $0.id == selectedDocumentId }
    }

    var selectedReview: ReviewResult? {
        reviews.first { $0.id == selectedReviewId }
    }

    func reviewForDocument(_ docId: String) -> ReviewResult? {
        reviews.first { $0.documentId == docId }
    }

    var totalIssues: Int {
        reviews.reduce(0) { $0 + $1.unresolvedIssueCount }
    }

    var highPriorityIssues: Int {
        reviews.reduce(0) { $0 + $1.highSeverityCount }
    }

    init() {
        serverURL = savedServerURL
    }

    func updateServerURL(_ url: String) {
        serverURL = url
        savedServerURL = url
    }
}
