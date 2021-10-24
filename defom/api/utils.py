import cv2

def expect(input, expected_type, field):
    if isinstance(input, expected_type):
        return input
    raise AssertionError("Invalid input for type", field)

