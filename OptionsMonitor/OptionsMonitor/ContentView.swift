import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            WatchlistView()
                .tabItem {
                    Label("Watchlist", systemImage: "list.bullet")
                }

            ScannerView()
                .tabItem {
                    Label("Scanner", systemImage: "antenna.radiowaves.left.and.right")
                }

            AlertsListView()
                .tabItem {
                    Label("Alerts", systemImage: "bell.badge")
                }
        }
    }
}
