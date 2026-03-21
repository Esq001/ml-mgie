// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "TaxReviewApp",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "TaxReviewApp", targets: ["TaxReviewApp"])
    ],
    targets: [
        .executableTarget(
            name: "TaxReviewApp",
            path: "Sources"
        )
    ]
)
