import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedTab = SidebarTab.dashboard
    @State private var previewingDocument: TaxDocument?

    enum SidebarTab: String, CaseIterable {
        case dashboard = "Dashboard"
        case documents = "Documents"
        case reviews = "Reviews"
        case compare = "Compare"
        case reports = "Reports"

        var icon: String {
            switch self {
            case .dashboard: return "gauge.with.dots.needle.33percent"
            case .documents: return "doc.on.doc"
            case .reviews: return "checkmark.shield"
            case .compare: return "arrow.left.arrow.right"
            case .reports: return "doc.richtext"
            }
        }
    }

    var body: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            ZStack {
                detailView

                // Error toast
                if let error = appState.errorMessage {
                    VStack {
                        Spacer()
                        errorToast(error)
                    }
                    .padding()
                    .transition(.move(edge: .bottom))
                }
            }
        }
        .navigationTitle("")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                serverStatusIndicator
            }
        }
        .sheet(item: $previewingDocument) { doc in
            DocumentPreviewView(document: doc)
                .environmentObject(appState)
                .frame(minWidth: 1000, minHeight: 700)
        }
        .onReceive(NotificationCenter.default.publisher(for: .previewDocument)) { notif in
            if let doc = notif.object as? TaxDocument {
                previewingDocument = doc
            }
        }
    }

    private var sidebar: some View {
        VStack(spacing: 0) {
            // App branding
            HStack(spacing: 10) {
                Image(systemName: "building.columns.fill")
                    .font(.title2)
                    .foregroundStyle(.blue)
                VStack(alignment: .leading, spacing: 1) {
                    Text("Tax Review")
                        .font(.headline)
                    Text("AI-Powered")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)

            Divider()

            List(SidebarTab.allCases, id: \.self, selection: $selectedTab) { tab in
                Label(tab.rawValue, systemImage: tab.icon)
                    .badge(badgeCount(for: tab))
            }
            .listStyle(.sidebar)

            Divider()

            // Quick stats at bottom
            VStack(spacing: 8) {
                quickStatRow("Documents", "\(appState.documents.count)", .blue)
                quickStatRow("Open Issues", "\(appState.totalIssues)", appState.highPriorityIssues > 0 ? .red : .orange)
            }
            .padding(12)
        }
        .frame(minWidth: 210)
    }

    private func quickStatRow(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack {
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(.caption.bold())
                .foregroundStyle(color)
        }
    }

    @ViewBuilder
    private var detailView: some View {
        switch selectedTab {
        case .dashboard:
            DashboardView()
        case .documents:
            DocumentsView()
        case .reviews:
            ReviewsListView()
        case .compare:
            CompareView()
        case .reports:
            ReportsView()
        }
    }

    private var serverStatusIndicator: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(appState.isLoading ? .orange : .green)
                .frame(width: 8, height: 8)
                .shadow(color: appState.isLoading ? .orange.opacity(0.5) : .green.opacity(0.5), radius: 4)
            Text(appState.isLoading ? "Working..." : "Connected")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(
            Capsule()
                .fill(.secondary.opacity(0.08))
        )
    }

    private func errorToast(_ message: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.red)
            Text(message)
                .font(.callout)
            Spacer()
            Button {
                withAnimation { appState.errorMessage = nil }
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(.red.opacity(0.08))
                .shadow(color: .black.opacity(0.1), radius: 8, y: 4)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(.red.opacity(0.2), lineWidth: 1)
        )
        .onAppear {
            DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                withAnimation { appState.errorMessage = nil }
            }
        }
    }

    private func badgeCount(for tab: SidebarTab) -> Int {
        switch tab {
        case .dashboard: return 0
        case .documents: return appState.documents.count
        case .reviews: return appState.totalIssues
        case .compare: return appState.comparisons.count
        case .reports: return 0
        }
    }
}

// MARK: - Notification for document preview

extension Notification.Name {
    static let previewDocument = Notification.Name("previewDocument")
}

// MARK: - Make TaxDocument identifiable for sheet

extension TaxDocument: @retroactive Hashable {
    public static func == (lhs: TaxDocument, rhs: TaxDocument) -> Bool {
        lhs.id == rhs.id
    }
    public func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}
