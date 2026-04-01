import SwiftUI

struct AlertsListView: View {
    @StateObject private var viewModel = AlertsViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.alerts.isEmpty {
                    ContentUnavailableView(
                        "No Alerts",
                        systemImage: "bell.slash",
                        description: Text("Create alerts from the option detail screen to get notified when conditions are met.")
                    )
                } else {
                    List {
                        Section {
                            ForEach(viewModel.alerts.filter(\.isActive)) { alert in
                                AlertRow(alert: alert) {
                                    viewModel.toggleAlert(id: alert.id)
                                }
                            }
                            .onDelete { offsets in
                                let activeAlerts = viewModel.alerts.filter(\.isActive)
                                let idsToRemove = offsets.map { activeAlerts[$0].id }
                                for id in idsToRemove {
                                    viewModel.removeAlert(id: id)
                                }
                            }
                        } header: {
                            if viewModel.alerts.contains(where: \.isActive) {
                                Text("Active")
                            }
                        }

                        let inactiveAlerts = viewModel.alerts.filter { !$0.isActive }
                        if !inactiveAlerts.isEmpty {
                            Section("Triggered / Inactive") {
                                ForEach(inactiveAlerts) { alert in
                                    AlertRow(alert: alert) {
                                        viewModel.toggleAlert(id: alert.id)
                                    }
                                }
                                .onDelete { offsets in
                                    let idsToRemove = offsets.map { inactiveAlerts[$0].id }
                                    for id in idsToRemove {
                                        viewModel.removeAlert(id: id)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Alerts")
            .toolbar {
                if !viewModel.alerts.isEmpty {
                    ToolbarItem(placement: .primaryAction) {
                        Button {
                            Task { await viewModel.evaluateAlerts() }
                        } label: {
                            if viewModel.isLoading {
                                ProgressView()
                            } else {
                                Image(systemName: "arrow.clockwise")
                            }
                        }
                    }
                }
            }
        }
    }
}

struct AlertRow: View {
    let alert: OptionAlert
    let onToggle: () -> Void

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(alert.displayDescription)
                    .font(.subheadline)
                    .foregroundColor(alert.isActive ? .primary : .secondary)

                Text(alert.contractSymbol)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Toggle("", isOn: Binding(
                get: { alert.isActive },
                set: { _ in onToggle() }
            ))
            .labelsHidden()
        }
        .padding(.vertical, 2)
    }
}
