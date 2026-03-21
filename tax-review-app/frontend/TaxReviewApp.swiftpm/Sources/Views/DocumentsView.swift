import SwiftUI

struct DocumentsView: View {
    @EnvironmentObject var appState: AppState
    @State private var isDragOver = false
    @State private var showFilePicker = false
    @State private var searchText = ""
    @State private var sortOrder = SortOrder.newest
    private let api = APIService()

    enum SortOrder: String, CaseIterable {
        case newest = "Newest"
        case oldest = "Oldest"
        case name = "Name"
        case type = "Type"
    }

    private var filteredDocuments: [TaxDocument] {
        var docs = appState.documents
        if !searchText.isEmpty {
            docs = docs.filter {
                $0.filename.localizedCaseInsensitiveContains(searchText) ||
                $0.documentType.displayName.localizedCaseInsensitiveContains(searchText)
            }
        }
        switch sortOrder {
        case .newest: return docs.reversed()
        case .oldest: return docs
        case .name: return docs.sorted { $0.filename < $1.filename }
        case .type: return docs.sorted { $0.documentType.rawValue < $1.documentType.rawValue }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            uploadArea
                .padding()

            Divider()

            // Search and sort bar
            if !appState.documents.isEmpty {
                HStack(spacing: 12) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Search documents...", text: $searchText)
                        .textFieldStyle(.plain)

                    Divider().frame(height: 20)

                    Picker("Sort", selection: $sortOrder) {
                        ForEach(SortOrder.allCases, id: \.self) { order in
                            Text(order.rawValue).tag(order)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 100)

                    Text("\(filteredDocuments.count) documents")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
                .background(.bar)

                Divider()
            }

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
            ZStack {
                Circle()
                    .fill(.blue.opacity(0.1))
                    .frame(width: 64, height: 64)
                Image(systemName: "arrow.up.doc.fill")
                    .font(.system(size: 28))
                    .foregroundStyle(.blue)
            }

            Text("Drop tax documents here")
                .font(.headline)

            Text("PDF, Excel, CSV, PNG, JPG, TIFF")
                .font(.caption)
                .foregroundStyle(.tertiary)

            Button {
                showFilePicker = true
            } label: {
                Label("Choose Files", systemImage: "folder")
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .frame(maxWidth: .infinity)
        .frame(height: 180)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .strokeBorder(
                    style: StrokeStyle(lineWidth: 2, dash: [10, 6])
                )
                .foregroundStyle(isDragOver ? .blue : .secondary.opacity(0.2))
        )
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(isDragOver ? .blue.opacity(0.03) : .clear)
        )
        .scaleEffect(isDragOver ? 1.01 : 1.0)
        .animation(.easeInOut(duration: 0.2), value: isDragOver)
        .onDrop(of: [.fileURL], isTargeted: $isDragOver) { providers in
            handleDrop(providers)
            return true
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 56))
                .foregroundStyle(.quaternary)
            Text("No documents uploaded yet")
                .font(.title3)
                .foregroundStyle(.secondary)
            Text("Upload tax returns and work papers to get started")
                .font(.callout)
                .foregroundStyle(.tertiary)
            Spacer()
        }
    }

    private var documentList: some View {
        ScrollView {
            LazyVStack(spacing: 8) {
                ForEach(filteredDocuments) { doc in
                    DocumentCard(document: doc, hasReview: appState.reviewForDocument(doc.id) != nil)
                        .contextMenu {
                            Button {
                                NotificationCenter.default.post(name: .previewDocument, object: doc)
                            } label: {
                                Label("Preview", systemImage: "eye")
                            }
                            Button {
                                reviewDocument(doc)
                            } label: {
                                Label("Review with Claude", systemImage: "sparkles")
                            }
                            Divider()
                            Button(role: .destructive) {
                                deleteDocument(doc)
                            } label: {
                                Label("Delete", systemImage: "trash")
                            }
                        }
                        .onTapGesture(count: 2) {
                            NotificationCenter.default.post(name: .previewDocument, object: doc)
                        }
                }
            }
            .padding()
        }
    }

    // MARK: - Actions

    private func handleFileImport(_ result: Result<[URL], Error>) {
        guard case .success(let urls) = result else { return }
        for url in urls { uploadFile(url) }
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
                withAnimation(.easeInOut(duration: 0.3)) {
                    appState.documents.append(doc)
                }
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
                withAnimation(.easeInOut(duration: 0.25)) {
                    appState.documents.removeAll { $0.id == doc.id }
                }
            } catch {
                appState.errorMessage = "Delete failed: \(error.localizedDescription)"
            }
        }
    }
}

// MARK: - Document Card

struct DocumentCard: View {
    let document: TaxDocument
    let hasReview: Bool
    @State private var isHovered = false

    var body: some View {
        HStack(spacing: 14) {
            // File type icon
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(colorForType.opacity(0.1))
                    .frame(width: 44, height: 44)
                Image(systemName: iconForType)
                    .font(.title3)
                    .foregroundStyle(colorForType)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(document.filename)
                    .font(.headline)
                    .lineLimit(1)

                HStack(spacing: 8) {
                    Text(document.documentType.displayName)
                        .font(.caption)
                        .padding(.horizontal, 7)
                        .padding(.vertical, 2)
                        .background(colorForType.opacity(0.08))
                        .foregroundStyle(colorForType)
                        .clipShape(Capsule())

                    Text(document.fileSizeFormatted)
                        .font(.caption)
                        .foregroundStyle(.tertiary)

                    if let pages = document.pageCount {
                        Text("\(pages) pages")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                }
            }

            Spacer()

            if hasReview {
                Image(systemName: "checkmark.shield.fill")
                    .foregroundStyle(.green)
                    .font(.title3)
            }

            Image(systemName: "chevron.right")
                .foregroundStyle(.quaternary)
                .font(.caption)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(.background)
                .shadow(color: .black.opacity(isHovered ? 0.06 : 0.02), radius: isHovered ? 8 : 4, y: isHovered ? 3 : 1)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.secondary.opacity(isHovered ? 0.15 : 0.08), lineWidth: 1)
        )
        .scaleEffect(isHovered ? 1.005 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isHovered)
        .onHover { isHovered = $0 }
    }

    private var iconForType: String {
        switch document.fileType {
        case "pdf": return "doc.fill"
        case "excel": return "tablecells.fill"
        case "csv": return "tablecells"
        case "image": return "photo.fill"
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
