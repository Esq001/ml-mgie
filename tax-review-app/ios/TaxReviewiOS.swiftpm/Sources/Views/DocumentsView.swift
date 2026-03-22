import SwiftUI
import UniformTypeIdentifiers

struct DocumentsView: View {
    @EnvironmentObject var appState: AppState
    @State private var showFilePicker = false
    @State private var showCamera = false
    @State private var searchText = ""
    @State private var selectedDocument: TaxDocument?
    private let api = APIService()

    private var filteredDocuments: [TaxDocument] {
        if searchText.isEmpty { return appState.documents }
        return appState.documents.filter {
            $0.filename.localizedCaseInsensitiveContains(searchText) ||
            $0.documentType.displayName.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        NavigationStack {
            Group {
                if appState.documents.isEmpty {
                    emptyState
                } else {
                    documentList
                }
            }
            .navigationTitle("Documents")
            .searchable(text: $searchText, prompt: "Search documents")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        Button {
                            showFilePicker = true
                        } label: {
                            Label("Choose File", systemImage: "folder")
                        }
                        Button {
                            showCamera = true
                        } label: {
                            Label("Scan Document", systemImage: "doc.viewfinder")
                        }
                    } label: {
                        Image(systemName: "plus.circle.fill")
                    }
                }
            }
            .fileImporter(
                isPresented: $showFilePicker,
                allowedContentTypes: [.pdf, .spreadsheet, .commaSeparatedText, .png, .jpeg, .tiff],
                allowsMultipleSelection: true
            ) { result in
                handleFileImport(result)
            }
            .sheet(item: $selectedDocument) { doc in
                NavigationStack {
                    DocumentDetailView(document: doc)
                        .environmentObject(appState)
                }
            }
            .refreshable {
                await fetchDocuments()
            }
        }
    }

    private var emptyState: some View {
        ContentUnavailableView {
            Label("No Documents", systemImage: "doc.text.magnifyingglass")
        } description: {
            Text("Upload tax returns and work papers to review them with AI")
        } actions: {
            Button {
                showFilePicker = true
            } label: {
                Label("Choose Files", systemImage: "folder")
            }
            .buttonStyle(.borderedProminent)
        }
    }

    private var documentList: some View {
        List {
            ForEach(filteredDocuments) { doc in
                Button {
                    selectedDocument = doc
                } label: {
                    DocumentRow(document: doc, hasReview: appState.reviewForDocument(doc.id) != nil)
                }
                .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                    Button(role: .destructive) {
                        deleteDocument(doc)
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                }
                .swipeActions(edge: .leading) {
                    Button {
                        reviewDocument(doc)
                    } label: {
                        Label("Review", systemImage: "sparkles")
                    }
                    .tint(.blue)
                }
            }
        }
        .listStyle(.insetGrouped)
    }

    // MARK: - Actions

    private func handleFileImport(_ result: Result<[URL], Error>) {
        guard case .success(let urls) = result else { return }
        for url in urls { uploadFile(url) }
    }

    private func uploadFile(_ url: URL) {
        Task {
            appState.isLoading = true
            defer { appState.isLoading = false }
            do {
                let doc = try await api.uploadDocument(baseURL: appState.serverURL, fileURL: url)
                withAnimation { appState.documents.append(doc) }
            } catch {
                appState.showError("Upload failed: \(error.localizedDescription)")
            }
        }
    }

    private func reviewDocument(_ doc: TaxDocument) {
        Task {
            appState.isLoading = true
            defer { appState.isLoading = false }
            do {
                let request = ReviewRequest(documentId: doc.id, reviewFocus: [], customInstructions: "")
                let review = try await api.reviewDocument(baseURL: appState.serverURL, request: request)
                appState.reviews.append(review)
            } catch {
                appState.showError("Review failed: \(error.localizedDescription)")
            }
        }
    }

    private func deleteDocument(_ doc: TaxDocument) {
        Task {
            do {
                try await api.deleteDocument(baseURL: appState.serverURL, id: doc.id)
                withAnimation { appState.documents.removeAll { $0.id == doc.id } }
            } catch {
                appState.showError("Delete failed: \(error.localizedDescription)")
            }
        }
    }

    private func fetchDocuments() async {
        do {
            appState.documents = try await api.fetchDocuments(baseURL: appState.serverURL)
        } catch {
            appState.showError("Fetch failed: \(error.localizedDescription)")
        }
    }
}

// MARK: - Document Row

struct DocumentRow: View {
    let document: TaxDocument
    let hasReview: Bool

    var body: some View {
        HStack(spacing: 14) {
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(document.documentType.color.opacity(0.12))
                    .frame(width: 44, height: 44)
                Image(systemName: document.documentType.icon)
                    .foregroundStyle(document.documentType.color)
                    .font(.title3)
            }

            VStack(alignment: .leading, spacing: 3) {
                Text(document.filename)
                    .font(.body)
                    .lineLimit(1)
                    .foregroundStyle(.primary)

                HStack(spacing: 6) {
                    Text(document.documentType.displayName)
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(document.documentType.color.opacity(0.1))
                        .foregroundStyle(document.documentType.color)
                        .clipShape(Capsule())

                    Text(document.fileSizeFormatted)
                        .font(.caption2)
                        .foregroundStyle(.tertiary)

                    if let pages = document.pageCount {
                        Text("\(pages)p")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                    }
                }
            }

            Spacer()

            if hasReview {
                Image(systemName: "checkmark.shield.fill")
                    .foregroundStyle(.green)
            }

            Image(systemName: "chevron.right")
                .font(.caption2)
                .foregroundStyle(.quaternary)
        }
        .padding(.vertical, 4)
    }
}
