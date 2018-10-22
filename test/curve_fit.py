import numpy.polynomial.polynomial as poly


if __name__ == "__main__":
    x_values = [318.339, 333.506, 353.089, 373.177, 393.213]
    y_values = [-.384, .476, .444, .104, -.544]
    y_values2 = [-.004, .016, .456, .464, -.344]

    coefficients = poly.polyfit(x_values, y_values, 4)
    derivative_coefficients = poly.polyder(coefficients)
    print("Coefficients: {}".format(coefficients))
    print("Derivative coefficients: {}".format(derivative_coefficients))
    print("Results: {}".format(poly.polyval(x_values, derivative_coefficients)))
