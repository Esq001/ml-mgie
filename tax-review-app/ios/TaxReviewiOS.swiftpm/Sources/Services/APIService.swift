import Foundation

actor APIService {
    private let session = URLSession.shared

    func uploadDocument(baseURL: String, fileURL: URL) async throws -> TaxDocument {
        let url = URL(string: "\(baseURL)/api/documents/upload")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let fileData = try Data(contentsOf: fileURL)
        let filename = fileURL.lastPathComponent

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        return try JSONDecoder().decode(TaxDocument.self, from: data)
    }

    func fetchDocuments(baseURL: String) async throws -> [TaxDocument] {
        let url = URL(string: "\(baseURL)/api/documents/")!
        let (data, response) = try await session.data(from: url)
        try validateResponse(response)
        return try JSONDecoder().decode([TaxDocument].self, from: data)
    }

    func deleteDocument(baseURL: String, id: String) async throws {
        let url = URL(string: "\(baseURL)/api/documents/\(id)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }

    func reviewDocument(baseURL: String, request: ReviewRequest) async throws -> ReviewResult {
        let url = URL(string: "\(baseURL)/api/reviews/review")!
        return try await postJSON(url: url, body: request)
    }

    func fetchReviews(baseURL: String) async throws -> [ReviewResult] {
        let url = URL(string: "\(baseURL)/api/reviews/")!
        let (data, response) = try await session.data(from: url)
        try validateResponse(response)
        return try JSONDecoder().decode([ReviewResult].self, from: data)
    }

    func resolveIssue(baseURL: String, reviewId: String, issueId: String) async throws -> ReviewIssue {
        let url = URL(string: "\(baseURL)/api/reviews/\(reviewId)/issues/\(issueId)/resolve")!
        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        return try JSONDecoder().decode(ReviewIssue.self, from: data)
    }

    func compareDocuments(baseURL: String, request: CompareRequest) async throws -> ComparisonResult {
        let url = URL(string: "\(baseURL)/api/reviews/compare")!
        return try await postJSON(url: url, body: request)
    }

    func generateReport(baseURL: String, request: ReportRequest) async throws -> ReportResponse {
        let url = URL(string: "\(baseURL)/api/reviews/report")!
        return try await postJSON(url: url, body: request)
    }

    func healthCheck(baseURL: String) async throws -> Bool {
        let url = URL(string: "\(baseURL)/health")!
        let (_, response) = try await session.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse else { return false }
        return httpResponse.statusCode == 200
    }

    private func postJSON<T: Encodable, R: Decodable>(url: URL, body: T) async throws -> R {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(body)
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        return try JSONDecoder().decode(R.self, from: data)
    }

    private func validateResponse(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            throw APIError.httpError(httpResponse.statusCode)
        }
    }
}

enum APIError: LocalizedError {
    case invalidResponse
    case httpError(Int)

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Invalid server response"
        case .httpError(let code): return "Server error (HTTP \(code))"
        }
    }
}
