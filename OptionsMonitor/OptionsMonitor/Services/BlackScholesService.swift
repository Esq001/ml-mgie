import Foundation

struct BlackScholesService {
    /// Risk-free interest rate (approximate US Treasury rate)
    static let riskFreeRate: Double = 0.045

    /// Calculate all Greeks for an option contract
    /// - Parameters:
    ///   - contract: The option contract
    ///   - underlyingPrice: Current price of the underlying stock
    /// - Returns: Contract with Greeks populated
    static func calculateGreeks(for contract: OptionContract, underlyingPrice: Double) -> OptionContract {
        let S = underlyingPrice
        let K = contract.strike
        let T = timeToExpiration(contract.expiration)
        let r = riskFreeRate
        let sigma = contract.impliedVolatility

        guard S > 0, K > 0, T > 0, sigma > 0 else {
            return contract
        }

        let d1 = self.d1(S: S, K: K, T: T, r: r, sigma: sigma)
        let d2 = d1 - sigma * sqrt(T)

        var updated = contract

        switch contract.contractType {
        case .call:
            updated.delta = cumulativeNormalDistribution(d1)
            updated.theta = callTheta(S: S, K: K, T: T, r: r, sigma: sigma, d1: d1, d2: d2)
        case .put:
            updated.delta = cumulativeNormalDistribution(d1) - 1.0
            updated.theta = putTheta(S: S, K: K, T: T, r: r, sigma: sigma, d1: d1, d2: d2)
        }

        updated.gamma = self.gamma(S: S, T: T, sigma: sigma, d1: d1)
        updated.vega = self.vega(S: S, T: T, d1: d1)

        return updated
    }

    /// Calculate Greeks for an array of contracts
    static func calculateGreeks(for contracts: [OptionContract], underlyingPrice: Double) -> [OptionContract] {
        contracts.map { calculateGreeks(for: $0, underlyingPrice: underlyingPrice) }
    }

    // MARK: - Black-Scholes Components

    /// d1 parameter
    private static func d1(S: Double, K: Double, T: Double, r: Double, sigma: Double) -> Double {
        (log(S / K) + (r + sigma * sigma / 2.0) * T) / (sigma * sqrt(T))
    }

    /// Gamma: rate of change of delta
    private static func gamma(S: Double, T: Double, sigma: Double, d1: Double) -> Double {
        normalPDF(d1) / (S * sigma * sqrt(T))
    }

    /// Vega: sensitivity to volatility (per 1% move, so divide by 100)
    private static func vega(S: Double, T: Double, d1: Double) -> Double {
        S * normalPDF(d1) * sqrt(T) / 100.0
    }

    /// Theta for calls (per day, so divide by 365)
    private static func callTheta(S: Double, K: Double, T: Double, r: Double, sigma: Double, d1: Double, d2: Double) -> Double {
        let term1 = -(S * normalPDF(d1) * sigma) / (2.0 * sqrt(T))
        let term2 = r * K * exp(-r * T) * cumulativeNormalDistribution(d2)
        return (term1 - term2) / 365.0
    }

    /// Theta for puts (per day, so divide by 365)
    private static func putTheta(S: Double, K: Double, T: Double, r: Double, sigma: Double, d1: Double, d2: Double) -> Double {
        let term1 = -(S * normalPDF(d1) * sigma) / (2.0 * sqrt(T))
        let term2 = r * K * exp(-r * T) * cumulativeNormalDistribution(-d2)
        return (term1 + term2) / 365.0
    }

    // MARK: - Time Calculation

    /// Time to expiration in years
    private static func timeToExpiration(_ expiration: Date) -> Double {
        let seconds = expiration.timeIntervalSince(Date())
        let years = seconds / (365.25 * 24 * 3600)
        return max(years, 1.0 / 365.25) // Minimum 1 day
    }

    // MARK: - Normal Distribution Functions

    /// Standard normal probability density function
    private static func normalPDF(_ x: Double) -> Double {
        exp(-x * x / 2.0) / sqrt(2.0 * .pi)
    }

    /// Cumulative normal distribution (approximation using error function)
    private static func cumulativeNormalDistribution(_ x: Double) -> Double {
        0.5 * (1.0 + erf(x / sqrt(2.0)))
    }
}
