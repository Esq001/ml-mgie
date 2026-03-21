import Foundation

// MARK: - Enums

enum ReviewStatus: String, Codable {
    case pending
    case inProgress = "in_progress"
    case completed
    case failed
}

enum IssueSeverity: String, Codable, CaseIterable {
    case high, medium, low, info

    var color: String {
        switch self {
        case .high: return "red"
        case .medium: return "orange"
        case .low: return "yellow"
        case .info: return "blue"
        }
    }
}

enum DocumentType: String, Codable, CaseIterable {
    case taxReturn = "tax_return"
    case workPaper = "work_paper"
    case schedule
    case supportingDoc = "supporting_doc"
    case other

    var displayName: String {
        switch self {
        case .taxReturn: return "Tax Return"
        case .workPaper: return "Work Paper"
        case .schedule: return "Schedule"
        case .supportingDoc: return "Supporting Document"
        case .other: return "Other"
        }
    }
}

// MARK: - Models

struct TaxDocument: Codable, Identifiable {
    let id: String
    let filename: String
    let fileType: String
    var documentType: DocumentType
    let uploadTime: String
    let sizeBytes: Int
    let pageCount: Int?
    let extractedText: String

    enum CodingKeys: String, CodingKey {
        case id, filename
        case fileType = "file_type"
        case documentType = "document_type"
        case uploadTime = "upload_time"
        case sizeBytes = "size_bytes"
        case pageCount = "page_count"
        case extractedText = "extracted_text"
    }

    var fileSizeFormatted: String {
        ByteCountFormatter.string(fromByteCount: Int64(sizeBytes), countStyle: .file)
    }
}

struct ReviewIssue: Codable, Identifiable {
    let id: String
    let severity: IssueSeverity
    let category: String
    let title: String
    let description: String
    let location: String
    let recommendation: String
    var resolved: Bool
}

struct ReviewResult: Codable, Identifiable {
    let id: String
    let documentId: String
    let status: ReviewStatus
    let startedAt: String?
    let completedAt: String?
    let summary: String
    var issues: [ReviewIssue]
    let keyFindings: [String]
    let taxYear: String
    let entityName: String
    let returnType: String
    let totalIncome: String
    let totalDeductions: String
    let taxLiability: String
    let rawAnalysis: String

    enum CodingKeys: String, CodingKey {
        case id, summary, issues, status
        case documentId = "document_id"
        case startedAt = "started_at"
        case completedAt = "completed_at"
        case keyFindings = "key_findings"
        case taxYear = "tax_year"
        case entityName = "entity_name"
        case returnType = "return_type"
        case totalIncome = "total_income"
        case totalDeductions = "total_deductions"
        case taxLiability = "tax_liability"
        case rawAnalysis = "raw_analysis"
    }

    var unresolvedIssueCount: Int {
        issues.filter { !$0.resolved }.count
    }

    var highSeverityCount: Int {
        issues.filter { $0.severity == .high && !$0.resolved }.count
    }
}

struct ComparisonResult: Codable, Identifiable {
    let id: String
    let documentIds: [String]
    let summary: String
    let discrepancies: [ReviewIssue]
    let reconciliationNotes: [String]
    let status: ReviewStatus

    enum CodingKeys: String, CodingKey {
        case id, summary, discrepancies, status
        case documentIds = "document_ids"
        case reconciliationNotes = "reconciliation_notes"
    }
}

// MARK: - Request Models

struct ReviewRequest: Codable {
    let documentId: String
    let reviewFocus: [String]
    let customInstructions: String

    enum CodingKeys: String, CodingKey {
        case documentId = "document_id"
        case reviewFocus = "review_focus"
        case customInstructions = "custom_instructions"
    }
}

struct CompareRequest: Codable {
    let documentIds: [String]
    let comparisonFocus: String

    enum CodingKeys: String, CodingKey {
        case documentIds = "document_ids"
        case comparisonFocus = "comparison_focus"
    }
}

struct ReportRequest: Codable {
    let reviewIds: [String]
    let includeDetails: Bool
    let reportFormat: String

    enum CodingKeys: String, CodingKey {
        case reviewIds = "review_ids"
        case includeDetails = "include_details"
        case reportFormat = "report_format"
    }
}

struct ReportResponse: Codable {
    let report: String
    let format: String
}
