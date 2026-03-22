import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appState: AppState
    @State private var serverURL = ""
    @State private var connectionStatus: ConnectionStatus = .unknown
    @State private var isTesting = false
    private let api = APIService()

    enum ConnectionStatus {
        case unknown, connected, failed(String)

        var color: Color {
            switch self {
            case .unknown: return .gray
            case .connected: return .green
            case .failed: return .red
            }
        }

        var label: String {
            switch self {
            case .unknown: return "Not tested"
            case .connected: return "Connected"
            case .failed(let msg): return msg
            }
        }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Server") {
                    TextField("Backend URL", text: $serverURL)
                        .textContentType(.URL)
                        .autocapitalization(.none)
                        .onAppear { serverURL = appState.serverURL }

                    HStack {
                        Button("Test Connection") {
                            testConnection()
                        }
                        .disabled(isTesting)

                        Spacer()

                        if isTesting {
                            ProgressView()
                        } else {
                            HStack(spacing: 4) {
                                Circle()
                                    .fill(connectionStatus.color)
                                    .frame(width: 8, height: 8)
                                Text(connectionStatus.label)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }

                    Button("Save") {
                        appState.updateServerURL(serverURL)
                    }
                    .disabled(serverURL == appState.serverURL)
                }

                Section("About") {
                    LabeledContent("Version", value: "1.0.0")
                    LabeledContent("API", value: "Claude AI")
                    LabeledContent("Documents", value: "\(appState.documents.count)")
                    LabeledContent("Reviews", value: "\(appState.reviews.count)")
                }

                Section("Data") {
                    Button("Refresh All Data") {
                        Task { await refreshAll() }
                    }
                }
            }
            .navigationTitle("Settings")
        }
    }

    private func testConnection() {
        Task {
            isTesting = true
            defer { isTesting = false }
            do {
                let ok = try await api.healthCheck(baseURL: serverURL)
                connectionStatus = ok ? .connected : .failed("Health check failed")
            } catch {
                connectionStatus = .failed(error.localizedDescription)
            }
        }
    }

    private func refreshAll() async {
        do {
            async let docs = api.fetchDocuments(baseURL: appState.serverURL)
            async let revs = api.fetchReviews(baseURL: appState.serverURL)
            appState.documents = try await docs
            appState.reviews = try await revs
        } catch {
            appState.showError("Refresh failed: \(error.localizedDescription)")
        }
    }
}
