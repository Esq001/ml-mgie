// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "TaxReviewiOS",
    platforms: [.iOS(.v17)],
    products: [
        .executable(name: "TaxReviewiOS", targets: ["TaxReviewiOS"])
    ],
    targets: [
        .executableTarget(
            name: "TaxReviewiOS",
            path: "Sources"
        )
    ]
)
