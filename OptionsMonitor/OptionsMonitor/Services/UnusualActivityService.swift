import Foundation

struct UnusualActivityService {

    /// Scan an options chain for unusual activity
    /// - Parameters:
    ///   - chain: The options chain to analyze
    ///   - minScore: Minimum score threshold to include (default 3.0)
    /// - Returns: Array of unusual activity items, sorted by score descending
    static func scan(chain: OptionsChain, minScore: Double = 3.0) -> [UnusualActivity] {
        let allContracts = chain.calls + chain.puts
        guard !allContracts.isEmpty else { return [] }

        // Calculate chain-wide statistics for relative scoring
        let volumes = allContracts.map { Double($0.volume) }
        let ivValues = allContracts.compactMap { $0.impliedVolatility > 0 ? $0.impliedVolatility : nil }

        let avgVolume = volumes.reduce(0, +) / Double(max(volumes.count, 1))
        let avgIV = ivValues.reduce(0, +) / Double(max(ivValues.count, 1))
        let maxIV = ivValues.max() ?? 1.0
        let minIV = ivValues.min() ?? 0.0
        let ivRange = max(maxIV - minIV, 0.001)

        var activities: [UnusualActivity] = []

        for contract in allContracts {
            var score: Double = 0
            var reasons: [String] = []

            // 1. Volume/OI Ratio scoring
            let voiRatio = contract.volumeToOIRatio
            if voiRatio > 5.0 {
                score += 3.0
                reasons.append(String(format: "Vol/OI ratio: %.1fx", voiRatio))
            } else if voiRatio > 2.0 {
                score += 2.0
                reasons.append(String(format: "Vol/OI ratio: %.1fx", voiRatio))
            } else if voiRatio > 1.0 {
                score += 1.0
                reasons.append(String(format: "Vol/OI ratio: %.1fx", voiRatio))
            }

            // 2. Volume spike vs chain average
            let volume = Double(contract.volume)
            if avgVolume > 0 && volume > 0 {
                let volumeMultiple = volume / avgVolume
                if volumeMultiple > 10.0 {
                    score += 3.0
                    reasons.append(String(format: "Volume %.0fx above average", volumeMultiple))
                } else if volumeMultiple > 5.0 {
                    score += 2.0
                    reasons.append(String(format: "Volume %.0fx above average", volumeMultiple))
                } else if volumeMultiple > 2.0 {
                    score += 1.0
                    reasons.append(String(format: "Volume %.1fx above average", volumeMultiple))
                }
            }

            // 3. IV Rank within the chain
            if contract.impliedVolatility > 0 {
                let ivRank = (contract.impliedVolatility - minIV) / ivRange
                if ivRank > 0.9 {
                    score += 2.0
                    reasons.append(String(format: "IV rank: %.0f%% (top of chain)", ivRank * 100))
                } else if ivRank > 0.75 {
                    score += 1.0
                    reasons.append(String(format: "IV rank: %.0f%%", ivRank * 100))
                }

                // IV significantly above chain average
                if avgIV > 0 {
                    let ivMultiple = contract.impliedVolatility / avgIV
                    if ivMultiple > 2.0 {
                        score += 1.5
                        reasons.append(String(format: "IV %.1fx chain average", ivMultiple))
                    }
                }
            }

            // 4. Large absolute volume
            if contract.volume > 5000 {
                score += 2.0
                reasons.append("Very high volume: \(formatNumber(contract.volume))")
            } else if contract.volume > 1000 {
                score += 1.0
                reasons.append("High volume: \(formatNumber(contract.volume))")
            }

            // 5. Large trade detection (high volume + high Vol/OI)
            if contract.volume > 1000 && voiRatio > 3.0 {
                score += 1.5
                reasons.append("Potential large block trade")
            }

            if score >= minScore && !reasons.isEmpty {
                activities.append(UnusualActivity(
                    contract: contract,
                    ticker: chain.ticker,
                    underlyingPrice: chain.underlyingPrice,
                    score: score,
                    reasons: reasons,
                    detectedAt: Date()
                ))
            }
        }

        return activities.sorted { $0.score > $1.score }
    }

    /// Scan multiple tickers for unusual activity
    static func scanMultiple(chains: [OptionsChain], minScore: Double = 3.0) -> [UnusualActivity] {
        chains.flatMap { scan(chain: $0, minScore: minScore) }
            .sorted { $0.score > $1.score }
    }

    private static func formatNumber(_ n: Int) -> String {
        if n >= 1_000_000 {
            return String(format: "%.1fM", Double(n) / 1_000_000)
        } else if n >= 1_000 {
            return String(format: "%.1fK", Double(n) / 1_000)
        }
        return "\(n)"
    }
}
