import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appState: AppState
    @State private var serverURL = ""
    @State private var connectionStatus = ""
    private let api = APIService()

    var body: some View {
        Form {
            Section("Server Connection") {
                TextField("Backend URL", text: $serverURL)
                    .textFieldStyle(.roundedBorder)
                    .onAppear { serverURL = appState.serverURL }

                HStack {
                    Button("Save") {
                        appState.updateServerURL(serverURL)
                    }
                    Button("Test Connection") {
                        testConnection()
                    }
                    if !connectionStatus.isEmpty {
                        Text(connectionStatus)
                            .foregroundStyle(connectionStatus.contains("OK") ? .green : .red)
                    }
                }
            }
        }
        .padding()
        .frame(width: 450, height: 200)
    }

    private func testConnection() {
        Task {
            do {
                let ok = try await api.healthCheck(baseURL: serverURL)
                connectionStatus = ok ? "OK" : "Failed"
            } catch {
                connectionStatus = "Error: \(error.localizedDescription)"
            }
        }
    }
}
