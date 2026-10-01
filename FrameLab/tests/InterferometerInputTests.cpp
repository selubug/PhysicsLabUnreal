#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <stdexcept>
#include "FrameLab/InterferometerInput.h"
#include "FrameLab/ClassicalEtherModel.h"
#include "FrameLab/SpecialRelativityModel.h"

namespace {
void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAILED: " << message << '\n';
        std::exit(EXIT_FAILURE);
    }
}
void rejects(double length, double wavelength, double speed, double angle) {
    try {
        (void)framelab::parametersFromDisplayUnits(length, wavelength, speed, angle);
        require(false, "invalid display input must throw");
    } catch (const std::invalid_argument&) {}
}
}

int main() {
    using namespace framelab;
    const auto p = parametersFromDisplayUnits(11, 500, 29780, 360);
    require(std::abs(p.wavelengthMeters - 500e-9) < 1e-21, "nm converts to meters");
    require(p.orientationDegrees == 0, "full turn normalizes to zero");
    const auto ether = ClassicalEtherModel{}.simulate(p);
    require(std::abs(ether.ninetyDegreeRotationFringeShift) > 0.35 &&
            std::abs(ether.ninetyDegreeRotationFringeShift) < 0.5, "converted default physical prediction");
    require(SpecialRelativityModel{}.simulate(p).fringeOffset == 0, "SR converted prediction");
    const auto negative = parametersFromDisplayUnits(11, 500, 29780, -315);
    require(std::abs(ClassicalEtherModel{}.simulate(negative).fringeOffset) < 1e-7,
            "negative equivalent angle agrees");
    rejects(0, 500, 29780, 0);
    rejects(11, 0, 29780, 0);
    rejects(11, 500, -1, 0);
    rejects(11, 500, constants::SpeedOfLightMetersPerSecond, 0);
    const double nan = std::numeric_limits<double>::quiet_NaN();
    rejects(nan, 500, 29780, 0);
    rejects(11, nan, 29780, 0);
    rejects(11, 500, nan, 0);
    rejects(11, 500, 29780, nan);
    rejects(11, std::numeric_limits<double>::infinity(), 29780, 0);
    rejects(11, std::numeric_limits<double>::denorm_min(), 29780, 0);
    std::cout << "Display input tests passed.\n";
}
