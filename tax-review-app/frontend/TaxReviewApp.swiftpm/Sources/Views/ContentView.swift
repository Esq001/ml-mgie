import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedTab = SidebarTab.documents

    enum SidebarTab: String, CaseIterable {
        case documents = "Documents"
        case reviews = "Reviews"
        case compare = "Compare"
        case reports = "Reports"

        var icon: String {
            switch self {
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
            detailView
        }
        .navigationTitle("Tax Review")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                serverStatusIndicator
            }
        }
    }

    private var sidebar: some View {
        List(SidebarTab.allCases, id: \.self, selection: $selectedTab) { tab in
            Label(tab.rawValue, systemImage: tab.icon)
                .badge(badgeCount(for: tab))
        }
        .listStyle(.sidebar)
        .frame(minWidth: 200)
    }

    @ViewBuilder
    private var detailView: some View {
        switch selectedTab {
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
        HStack(spacing: 4) {
            Circle()
                .fill(appState.isLoading ? .orange : .green)
                .frame(width: 8, height: 8)
            Text(appState.isLoading ? "Working..." : "Connected")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private func badgeCount(for tab: SidebarTab) -> Int {
        switch tab {
        case .documents: return appState.documents.count
        case .reviews: return appState.totalIssues
        case .compare: return appState.comparisons.count
        case .reports: return 0
        }
    }
}
