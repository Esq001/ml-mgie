import SwiftUI

@main
struct TaxReviewApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .frame(minWidth: 1200, minHeight: 800)
        }
        .windowStyle(.titleBar)
        .defaultSize(width: 1400, height: 900)

        Settings {
            SettingsView()
                .environmentObject(appState)
        }
    }
}
