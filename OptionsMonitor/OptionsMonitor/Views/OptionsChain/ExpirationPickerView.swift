import SwiftUI

struct ExpirationPickerView: View {
    let dates: [Date]
    @Binding var selectedDate: Date?

    private let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMM d"
        return f
    }()

    private let fullDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMM d, yyyy"
        return f
    }()

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(dates, id: \.self) { date in
                    Button {
                        selectedDate = date
                    } label: {
                        VStack(spacing: 2) {
                            Text(dateFormatter.string(from: date))
                                .font(.caption)
                                .fontWeight(isSelected(date) ? .bold : .regular)
                            Text(daysUntil(date))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(
                            isSelected(date)
                                ? Color.accentColor.opacity(0.15)
                                : Color(.systemGray6)
                        )
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(isSelected(date) ? Color.accentColor : Color.clear, lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
        }
    }

    private func isSelected(_ date: Date) -> Bool {
        guard let selected = selectedDate else { return false }
        return Calendar.current.isDate(date, inSameDayAs: selected)
    }

    private func daysUntil(_ date: Date) -> String {
        let days = Calendar.current.dateComponents([.day], from: Date(), to: date).day ?? 0
        if days == 0 { return "Today" }
        if days == 1 { return "1d" }
        return "\(days)d"
    }
}
