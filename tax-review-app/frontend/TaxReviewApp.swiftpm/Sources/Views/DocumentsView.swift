import SwiftUI

struct DocumentsView: View {
    @EnvironmentObject var appState: AppState
    @State private var isDragOver = false
    @State private var showFilePicker = false
    private let api = APIService()

    var body: some View {
        VStack(spacing: 0) {
            // Header with upload area
            uploadArea
                .padding()

            Divider()

            // Document list
            if appState.documents.isEmpty {
                emptyState
            } else {
                documentList
            }
        }
        .fileImporter(
            isPresented: $showFilePicker,
            allowedContentTypes: [.pdf, .spreadsheet, .commaSeparatedText, .png, .jpeg, .tiff],
            allowsMultipleSelection: true
        ) { result in
            handleFileImport(result)
        }
    }

    private var uploadArea: some View {
        VStack(spacing: 12) {
            Image(systemName: "arrow.up.doc")
                .font(.system(size: 36))
                .foregroundStyle(.secondary)

            Text("Drop tax documents here or click to upload")
                .font(.headline)
                .foregroundStyle(.secondary)

            Text("Supports PDF, Excel, CSV, PNG, JPG, TIFF")
                .font(.caption)
                .foregroundStyle(.tertiary)

            Button("Choose Files") {
                showFilePicker = true
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 160)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(
                    style: StrokeStyle(lineWidth: 2, dash: [8])
                )
                .foregroundStyle(isDragOver ? .blue : .secondary.opacity(0.3))
        )
        .onDrop(of: [.fileURL], isTargeted: $isDragOver) { providers in
            handleDrop(providers)
            return true
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("No documents uploaded yet")
                .font(.title3)
                .foregroundStyle(.secondary)
            Text("Upload tax returns and work papers to get started")
                .foregroundStyle(.tertiary)
            Spacer()
        }
    }

    private var documentList: some View {
        List(appState.documents) { doc in
            DocumentRow(document: doc)
                .contextMenu {
                    Button("Review Document") {
                        reviewDocument(doc)
                    }
                    Divider()
                    Button("Delete", role: .destructive) {
                        deleteDocument(doc)
                    }
                }
        }
    }

    // MARK: - Actions

    private func handleFileImport(_ result: Result<[URL], Error>) {
        guard case .success(let urls) = result else { return }
        for url in urls {
            uploadFile(url)
        }
    }

    private func handleDrop(_ providers: [NSItemProvider]) {
        for provider in providers {
            provider.loadItem(forTypeIdentifier: "public.file-url") { data, _ in
                guard let data = data as? Data,
                      let url = URL(dataRepresentation: data, relativeTo: nil)
                else { return }
                uploadFile(url)
            }
        }
    }

    private func uploadFile(_ url: URL) {
        Task {
            appState.isLoading = true
            defer { appState.isLoading = false }
            do {
                let doc = try await api.uploadDocument(
                    baseURL: appState.serverURL, fileURL: url
                )
                appState.documents.append(doc)
            } catch {
                appState.errorMessage = "Upload failed: \(error.localizedDescription)"
            }
        }
    }

    private func reviewDocument(_ doc: TaxDocument) {
        Task {
            appState.isLoading = true
            defer { appState.isLoading = false }
            do {
                let request = ReviewRequest(
                    documentId: doc.id, reviewFocus: [], customInstructions: ""
                )
                let review = try await api.reviewDocument(
                    baseURL: appState.serverURL, request: request
                )
                appState.reviews.append(review)
            } catch {
                appState.errorMessage = "Review failed: \(error.localizedDescription)"
            }
        }
    }

    private func deleteDocument(_ doc: TaxDocument) {
        Task {
            do {
                try await api.deleteDocument(baseURL: appState.serverURL, id: doc.id)
                appState.documents.removeAll { $0.id == doc.id }
            } catch {
                appState.errorMessage = "Delete failed: \(error.localizedDescription)"
            }
        }
    }
}

// MARK: - Document Row

struct DocumentRow: View {
    let document: TaxDocument

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: iconForType)
                .font(.title2)
                .foregroundStyle(colorForType)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 4) {
                Text(document.filename)
                    .font(.headline)
                HStack(spacing: 8) {
                    Text(document.documentType.displayName)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.secondary.opacity(0.15))
                        .clipShape(Capsule())

                    Text(document.fileSizeFormatted)
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    if let pages = document.pageCount {
                        Text("\(pages) pages")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()
        }
        .padding(.vertical, 4)
    }

    private var iconForType: String {
        switch document.fileType {
        case "pdf": return "doc.fill"
        case "excel": return "tablecells"
        case "csv": return "tablecells"
        case "image": return "photo"
        default: return "doc"
        }
    }

    private var colorForType: Color {
        switch document.documentType {
        case .taxReturn: return .blue
        case .workPaper: return .green
        case .schedule: return .purple
        case .supportingDoc: return .orange
        case .other: return .gray
        }
    }
}
